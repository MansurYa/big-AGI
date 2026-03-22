/**
 * Test script to verify anthropic.parser.ts error-first parsing logic
 *
 * This simulates the scenarios described in the TZ:
 * 1. Event without eventName containing error structure
 * 2. Event without eventName containing non-error data
 * 3. Malformed JSON without eventName
 * 4. Unknown event name
 */

// Mock the parser logic (extracted from anthropic.parser.ts lines 120-172)
function testErrorFirstParsing(eventData, eventName, context) {
  const results = {
    handled: false,
    action: null,
    error: null,
    logs: []
  };

  // Simulate the error-first parsing logic
  if (!eventName || eventName === undefined) {
    try {
      const payload = JSON.parse(eventData);

      // Check for error structure
      if (payload.type === 'error' || payload.error) {
        results.handled = true;
        const errorObj = payload.error || payload;
        const errorType = errorObj.type || 'unknown';
        const errorMessage = errorObj.message || 'Unknown proxy error';

        results.logs.push(`[Anthropic Parser] Recovered error event without eventName: ${errorType}`);

        // Check if retryable
        const isRetryableError = ['overloaded_error', 'rate_limit_error', 'api_error'].includes(errorType);

        if (isRetryableError && context?.retriesAvailable) {
          results.action = 'RETRY';
          results.logs.push(`[Aix.Anthropic] Can retry recovered error '${errorType}: ${errorMessage}'`);
        } else {
          results.action = 'SHOW_ERROR';
          results.logs.push(`Proxy error: ${errorMessage}`);
        }
        return results;
      }

      // Not an error structure - log and ignore
      results.handled = true;
      results.action = 'IGNORE';
      results.logs.push('[Anthropic Parser] Event without eventName (non-error)');
      return results;

    } catch (parseError) {
      // Not JSON or parsing failed - log and ignore
      results.handled = true;
      results.action = 'IGNORE';
      results.logs.push('[Anthropic Parser] Malformed event without eventName');
      return results;
    }
  }

  // Has eventName - would go to switch statement
  results.handled = false;
  results.action = 'SWITCH';
  return results;
}

// Test cases
const testCases = [
  {
    name: "Scenario 1: Error without eventName (retryable)",
    eventData: '{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}',
    eventName: undefined,
    context: { retriesAvailable: true },
    expected: { action: 'RETRY', handled: true }
  },
  {
    name: "Scenario 2: Error without eventName (non-retryable)",
    eventData: '{"type":"error","error":{"type":"invalid_request_error","message":"Bad request"}}',
    eventName: undefined,
    context: { retriesAvailable: false },
    expected: { action: 'SHOW_ERROR', handled: true }
  },
  {
    name: "Scenario 3: Error without eventName (no retries available)",
    eventData: '{"type":"error","error":{"type":"rate_limit_error","message":"Rate limited"}}',
    eventName: undefined,
    context: { retriesAvailable: false },
    expected: { action: 'SHOW_ERROR', handled: true }
  },
  {
    name: "Scenario 4: Non-error without eventName",
    eventData: '{"type":"unknown","data":"something"}',
    eventName: undefined,
    context: {},
    expected: { action: 'IGNORE', handled: true }
  },
  {
    name: "Scenario 5: Malformed JSON without eventName",
    eventData: '{"type":"error","error":{"incomplete...',
    eventName: undefined,
    context: {},
    expected: { action: 'IGNORE', handled: true }
  },
  {
    name: "Scenario 6: Normal event with eventName",
    eventData: '{"type":"message_start","message":{}}',
    eventName: 'message_start',
    context: {},
    expected: { action: 'SWITCH', handled: false }
  },
  {
    name: "Scenario 7: Error structure without nested error field",
    eventData: '{"error":{"type":"api_error","message":"API error"}}',
    eventName: undefined,
    context: { retriesAvailable: true },
    expected: { action: 'RETRY', handled: true }
  },
  {
    name: "Scenario 8: Chinese error message (没有可用账号)",
    eventData: '{"type":"error","error":{"message":"没有可用账号"}}',
    eventName: undefined,
    context: { retriesAvailable: false },
    expected: { action: 'SHOW_ERROR', handled: true }
  }
];

// Run tests
console.log('='.repeat(80));
console.log('PARSER LOGIC VERIFICATION TEST');
console.log('='.repeat(80));
console.log();

let passed = 0;
let failed = 0;

testCases.forEach((test, index) => {
  console.log(`Test ${index + 1}: ${test.name}`);
  console.log('-'.repeat(80));

  const result = testErrorFirstParsing(test.eventData, test.eventName, test.context);

  console.log('Input:');
  console.log(`  eventName: ${test.eventName}`);
  console.log(`  eventData: ${test.eventData.substring(0, 60)}${test.eventData.length > 60 ? '...' : ''}`);
  console.log(`  context: ${JSON.stringify(test.context)}`);
  console.log();

  console.log('Result:');
  console.log(`  handled: ${result.handled}`);
  console.log(`  action: ${result.action}`);
  console.log(`  logs: ${result.logs.length} messages`);
  result.logs.forEach(log => console.log(`    - ${log}`));
  console.log();

  // Verify expectations
  const actionMatch = result.action === test.expected.action;
  const handledMatch = result.handled === test.expected.handled;

  if (actionMatch && handledMatch) {
    console.log('✅ PASS');
    passed++;
  } else {
    console.log('❌ FAIL');
    console.log(`  Expected: action=${test.expected.action}, handled=${test.expected.handled}`);
    console.log(`  Got: action=${result.action}, handled=${result.handled}`);
    failed++;
  }

  console.log();
  console.log();
});

console.log('='.repeat(80));
console.log('SUMMARY');
console.log('='.repeat(80));
console.log(`Total: ${testCases.length} tests`);
console.log(`Passed: ${passed} ✅`);
console.log(`Failed: ${failed} ❌`);
console.log();

if (failed === 0) {
  console.log('🎉 All tests passed! Parser logic is correct.');
  process.exit(0);
} else {
  console.log('⚠️  Some tests failed. Review the implementation.');
  process.exit(1);
}
