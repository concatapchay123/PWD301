const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadApiClient(fetchMock) {
  const window = {
    location: { reload: () => {} },
  };
  const document = {
    querySelector: () => null,
  };
  const context = {
    window,
    document,
    fetch: fetchMock,
    console,
    FormData: class {},
  };
  vm.createContext(context);
  const apiPath = path.resolve(__dirname, '../../frontend/assets/js/api.js');
  vm.runInContext(fs.readFileSync(apiPath, 'utf8'), context, { filename: apiPath });
  return context.window.ApiClient;
}

test('SYNC-046: rejects HTTP 200 with success: false and preserves domain errors', async () => {
  const ApiClient = loadApiClient(async () => {
    return {
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({
        success: false,
        error: {
          code: 'ASSESSMENT_LOCKED',
          message: 'Bài thi đã bị khóa, không thể nộp thêm câu hỏi.',
        },
      }),
    };
  });

  await assert.rejects(
    async () => {
      await ApiClient.request('/test/endpoint');
    },
    (err) => {
      assert.equal(err.status, 200);
      assert.equal(err.code, 'ASSESSMENT_LOCKED');
      assert.match(err.message, /Bài thi đã bị khóa/);
      assert.equal(err.rawMessage, 'Bài thi đã bị khóa, không thể nộp thêm câu hỏi.');
      return true;
    }
  );
});

test('SYNC-046: rejects unexpected HTML page in API response', async () => {
  const htmlSnippets = [
    '<!DOCTYPE html><html><body>Error</body></html>',
    '  <!doctype html> <head></head>',
    '<html><head><title>Login Required</title></head></html>',
  ];

  for (const snippet of htmlSnippets) {
    const ApiClient = loadApiClient(async () => {
      return {
        ok: true,
        status: 200,
        headers: { get: () => 'text/html; charset=utf-8' },
        text: async () => snippet,
      };
    });

    await assert.rejects(
      async () => {
        await ApiClient.request('/test/html');
      },
      (err) => {
        assert.match(err.message, /Máy chủ trả về trang HTML ngoài dự kiến/);
        return true;
      }
    );
  }
});

test('SYNC-046: HTTP 202 Accepted with valid JSON is accepted and not blanket-rejected', async () => {
  const ApiClient = loadApiClient(async () => {
    return {
      ok: true,
      status: 202,
      headers: { get: () => 'application/json' },
      json: async () => ({
        success: true,
        status: 'PENDING_APPROVAL',
        data: { changeset_id: 123 },
      }),
    };
  });

  const res = await ApiClient.request('/test/async-action');
  assert.equal(res.success, true);
  assert.equal(res.status, 'PENDING_APPROVAL');
  assert.equal(res.data.changeset_id, 123);
});

test('SYNC-046: _allowFailure allows caller to inspect raw failure if needed', async () => {
  const ApiClient = loadApiClient(async () => {
    return {
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({
        success: false,
        error: { code: 'PROBE_CHECK' },
      }),
    };
  });

  const res = await ApiClient.request('/test/probe', { _allowFailure: true });
  assert.equal(res.success, false);
  assert.equal(res.error.code, 'PROBE_CHECK');
});
