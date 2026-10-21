import asyncio

from utils.browser import auth_error_categories, log_auth_page_state, log_auth_response


class Response:
	url = 'https://example.test/api/user/login?token=secret-query'
	status = 200

	async def json(self):
		return {
			'success': False,
			'message': '用户名或密码错误 secret-message',
			'data': {'session': 'secret-cookie', 'password': 'secret-password'},
		}


def test_response_logs_only_metadata(capsys):
	asyncio.run(log_auth_response(Response()))
	output = capsys.readouterr().out
	assert 'status=200 success=False' in output
	assert 'credentials_rejected' in output
	assert 'secret-' not in output
	assert 'example.test' not in output


def test_non_json_and_unrelated_responses(capsys):
	class NonJson(Response):
		status = 403

		async def json(self):
			raise ValueError('secret-response-body')

	asyncio.run(log_auth_response(NonJson()))
	output = capsys.readouterr().out
	assert 'status=403 format=non_json' in output
	assert 'secret-' not in output
	response = Response()
	response.url = 'https://example.test/api/token?key=secret-token'
	asyncio.run(log_auth_response(response))
	assert capsys.readouterr().out == ''


def test_page_logs_no_text_or_query(capsys):
	class Page:
		url = 'https://example.test/login?session=secret-session'

		async def evaluate(self, expression):
			return {'text': '操作过于频繁，请稍后再试 secret-page', 'alertCount': 1, 'passwordForm': True}

	asyncio.run(log_auth_page_state(Page()))
	output = capsys.readouterr().out
	assert 'page=/login' in output
	assert 'rate_limited' in output
	assert 'secret-' not in output


def test_unknown_messages_are_not_copied():
	assert auth_error_categories('secret-token-or-personal-message') == []
	assert auth_error_categories({'password': 'secret-password'}) == []
	assert auth_error_categories('请进行验证 captcha') == ['challenge_required']
