"""Configured-worker restrictions; these mocks do not prove an OS sandbox."""
import json
from pathlib import Path
import subprocess
import tomllib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from llm.backends import codex_cli


CAPABILITIES = ('shell_tool', 'apps', 'view_image', 'hooks', 'plugins', 'multi_agent',
                'code_mode', 'computer_use', 'browser_use', 'image_generation')


def jsonl(*items):
    return '\n'.join(json.dumps(row) for row in items)


@pytest.fixture
def worker(monkeypatch, tmp_path):
    monkeypatch.setenv('AUTORTL_CODEX_BIN', 'configured-codex.exe')
    monkeypatch.setattr(codex_cli.tempfile, 'tempdir', str(tmp_path))
    calls = []
    process = Mock(returncode=0, pid=12345)
    process.communicate.return_value = (jsonl({'type': 'thread.started', 'thread_id': 'safe-session'},
                                             {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'RTL'}},
                                             {'type': 'turn.completed'}), '')

    def spawn(command, **kwargs):
        calls.append(('worker', command, kwargs))
        Path(command[command.index('--output-last-message') + 1]).write_text('module m; endmodule', encoding='utf-8')
        return process

    def listing(command, **kwargs):
        calls.append(('listing', command, kwargs))
        overrides = [command[i+1] for i, arg in enumerate(command[:-1]) if arg in ('-c', '--config')]
        server_policy = next(value for value in overrides if value.startswith('mcp_servers='))
        policy = tomllib.loads(server_policy)['mcp_servers']
        # Empty map does not erase inherited servers in the observed CLI.
        rows = (json.loads((Path(__file__).parent / 'fixtures' / 'codex_mcp_inventory.json').read_text(encoding='utf-8'))
                if not policy else [{'name': name, 'enabled': values['enabled']} for name, values in policy.items()])
        return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr='')

    monkeypatch.setattr(codex_cli.subprocess, 'run', listing)
    monkeypatch.setattr(codex_cli.subprocess, 'Popen', spawn)
    return calls, process


def test_effective_mcp_is_disabled_before_worker_and_security_env_is_preserved(monkeypatch, worker):
    calls, _ = worker
    protected = {'CODEX_HOME': 'existing-auth-home', 'CODEX_PERMISSION_PROFILE': 'managed',
                 'CODEX_SANDBOX_NETWORK_DISABLED': '1', 'CODEX_APP_TOOLS_PIPE_PATH': 'existing-tool-pipe'}
    for key, value in protected.items():
        monkeypatch.setenv(key, value)
    response, metadata = codex_cli.ask('specified-model', 'request', timeout_s=12)
    assert response.startswith('module m')
    assert metadata['worker_policy'] == 'restricted_text_v1'
    assert metadata['mcp_configuration_checked'] is True and metadata['tool_items_observed'] == 0
    assert [row[0] for row in calls] == ['listing', 'listing', 'worker']
    for _, command, kwargs in calls:
        assert kwargs.get('shell') is False
        assert kwargs.get('env') is None  # Existing auth/managed security environment inherited unchanged.
        disabled = [command[i+1] for i, arg in enumerate(command[:-1]) if arg == '--disable']
        assert set(CAPABILITIES) <= set(disabled)
        assert 'web_search="disabled"' in command
    worker_command = calls[-1][1]
    assert '--ignore-user-config' in worker_command and '--strict-config' in worker_command
    assert '--ignore-rules' not in worker_command
    assert not any('bypass' in arg for arg in worker_command)
    assert worker_command[worker_command.index('--sandbox')+1] == 'read-only'
    assert worker_command[worker_command.index('--model')+1] == 'specified-model'
    policy = tomllib.loads(next(arg for arg in worker_command if arg.startswith('mcp_servers=')))['mcp_servers']
    assert set(policy) == {'node_repl', 'managed-fpga'}
    assert all(value == {'enabled': False, 'command': '__autortl_disabled_mcp__'} for value in policy.values())
    assert all(codex_cli.os.environ.get(key) == value for key, value in protected.items())


@pytest.mark.parametrize('payload', [None, {}, '[]', [{'name': 'x'}], [{'name': 'x', 'enabled': 0}],
                                     [{'name': 'x', 'enabled': True}, {'name': 'x', 'enabled': False}],
                                     [{'name': '\n', 'enabled': False}], [{'name': '\ud800', 'enabled': False}],
                                     [{'name': str(i), 'enabled': False} for i in range(129)],
                                     [{'name': 'x'*201, 'enabled': False}]])
def test_unprovable_mcp_config_blocks_worker(monkeypatch, worker, payload):
    calls, _ = worker
    monkeypatch.setattr(codex_cli.subprocess, 'run', Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr='')))
    with pytest.raises(codex_cli.CodexError, match='CODEX_PROTOCOL'):
        codex_cli.ask('default', 'request')
    assert not any(row[0] == 'worker' for row in calls)


def test_enabled_managed_or_new_server_blocks_worker(monkeypatch, worker):
    calls, _ = worker
    monkeypatch.setattr(codex_cli.subprocess, 'run', Mock(return_value=SimpleNamespace(returncode=0, stdout='[{"name":"forced-server","enabled":true}]', stderr='')))
    with pytest.raises(codex_cli.CodexError, match='CODEX_PROTOCOL'):
        codex_cli.ask('default', 'request')
    assert not any(row[0] == 'worker' for row in calls)


def test_unsupported_cli_restriction_fails_without_weaker_retry(monkeypatch, worker):
    calls, _ = worker
    listing = Mock(return_value=SimpleNamespace(returncode=2, stdout='', stderr='unsupported flag; private configuration detail'))
    monkeypatch.setattr(codex_cli.subprocess, 'run', listing)
    with pytest.raises(codex_cli.CodexError, match='CODEX_UNAVAILABLE') as error:
        codex_cli.ask('default', 'request')
    assert listing.call_count == 1
    assert 'private configuration detail' not in str(error.value)
    assert not any(row[0] == 'worker' for row in calls)


def test_config_preflight_timeout_blocks_worker(monkeypatch, worker):
    calls, _ = worker
    monkeypatch.setattr(codex_cli.subprocess, 'run', Mock(side_effect=subprocess.TimeoutExpired('codex', 1)))
    with pytest.raises(codex_cli.CodexError, match='CODEX_TIMEOUT'):
        codex_cli.ask('default', 'request', timeout_s=1)
    assert not any(row[0] == 'worker' for row in calls)


def test_config_output_byte_limit_blocks_worker(monkeypatch, worker):
    calls, _ = worker
    huge = '[{"name":"node_repl","enabled":false,"private":"' + 'x'*(256*1024) + '"}]'
    monkeypatch.setattr(codex_cli.subprocess, 'run', Mock(return_value=SimpleNamespace(returncode=0, stdout=huge, stderr='')))
    with pytest.raises(codex_cli.CodexError, match='CODEX_PROTOCOL'):
        codex_cli.ask('default', 'request')
    assert not any(row[0] == 'worker' for row in calls)


def test_preflights_and_execution_share_one_deadline(monkeypatch, worker):
    calls, process = worker
    clock = {'now': 100.0}
    monkeypatch.setattr(codex_cli.time, 'monotonic', lambda: clock['now'])
    listing = codex_cli.subprocess.run
    def spend_two_seconds(*args, **kwargs):
        response = listing(*args, **kwargs)
        clock['now'] += 2
        return response
    monkeypatch.setattr(codex_cli.subprocess, 'run', spend_two_seconds)
    codex_cli.ask('default', 'request', timeout_s=12)
    assert [row[2]['timeout'] for row in calls if row[0] == 'listing'] == [10, 10]
    assert process.communicate.call_args.kwargs['timeout'] == 8


def test_expired_configuration_deadline_never_spawns_worker(monkeypatch, worker):
    calls, _ = worker
    clock = {'now': 100.0}
    monkeypatch.setattr(codex_cli.time, 'monotonic', lambda: clock['now'])
    def late_configuration(executable, directory, deadline):
        clock['now'] = deadline + 1
        return []
    monkeypatch.setattr(codex_cli, '_worker_config', late_configuration, raising=False)
    cleanup = Mock()
    monkeypatch.setattr(codex_cli, '_terminate_worker', cleanup)
    with pytest.raises(codex_cli.CodexError, match='CODEX_TIMEOUT'):
        codex_cli.ask('default', 'request', timeout_s=12)
    assert not any(row[0] == 'worker' for row in calls)
    cleanup.assert_not_called()


def test_server_names_are_toml_data_and_cannot_inject_policy(monkeypatch, worker):
    calls, _ = worker
    name = 'node".tricky]=name'
    listing = Mock(side_effect=[SimpleNamespace(returncode=0, stdout=json.dumps([{'name': name, 'enabled': True}]), stderr=''),
                                SimpleNamespace(returncode=0, stdout=json.dumps([{'name': name, 'enabled': False}]), stderr='')])
    monkeypatch.setattr(codex_cli.subprocess, 'run', listing)
    codex_cli.ask('default', 'request')
    worker_command = next(row[1] for row in calls if row[0] == 'worker')
    policy = tomllib.loads(next(arg for arg in worker_command if arg.startswith('mcp_servers=')))
    assert policy == {'mcp_servers': {name: {'command': '__autortl_disabled_mcp__', 'enabled': False}}}


@pytest.mark.parametrize('item_type', ['command_execution', 'mcp_tool_call', 'file_change', 'web_search',
                                       'collab_agent_tool_call', 'todo_list', 'future_tool_type'])
@pytest.mark.parametrize('event_type', ['item.started', 'item.updated', 'item.completed'])
def test_tools_and_unknown_item_types_reject_even_completed_turn(item_type, event_type):
    events = jsonl({'type': event_type, 'item': {'type': item_type, 'arguments': {'secret': 'do-not-retain'}}},
                   {'type': 'turn.completed'})
    with pytest.raises(codex_cli.CodexError, match='CODEX_PROTOCOL') as error:
        codex_cli._parse_events(events)
    assert 'do-not-retain' not in str(error.value) and 'do-not-retain' not in json.dumps(error.value.metadata)


@pytest.mark.parametrize('event', [{'type': 'item.completed'}, {'type': 'item.started', 'item': []},
                                  {'type': 'item.updated', 'item': {'text': 'missing-type'}},
                                  {'type': 'item.updated', 'item': {'type': []}},
                                  {'type': 'future.unrecognized.event'}])
def test_unknown_event_shapes_fail_closed(event):
    with pytest.raises(codex_cli.CodexError, match='CODEX_PROTOCOL'):
        codex_cli._parse_events(jsonl(event, {'type': 'turn.completed'}))


def test_text_and_reasoning_items_remain_supported():
    events = jsonl({'type': 'thread.started', 'thread_id': 'session'}, {'type': 'turn.started'},
                   {'type': 'item.started', 'item': {'type': 'reasoning', 'text': 'planning'}},
                   {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'answer'}},
                   {'type': 'turn.completed', 'usage': {'input_tokens': 4, 'output_tokens': 2}})
    metadata = codex_cli._parse_events(events)
    assert metadata['session_id'] == 'session' and metadata['usage']['output_tokens'] == 2


def test_tool_fixture_rejected_through_public_adapter(worker):
    _, process = worker
    fixture = Path(__file__).parent / 'fixtures' / 'codex_unexpected_tool.jsonl'
    process.communicate.return_value = (fixture.read_text(encoding='utf-8'), '')
    with pytest.raises(codex_cli.CodexError, match='CODEX_PROTOCOL'):
        codex_cli.ask('default', 'request')
