import { apiAsync } from '~/common/util/trpc.client';

import type { AnthropicAccessSchema } from '../../server/anthropic/anthropic.access';
import type { IModelVendor } from '../IModelVendor';


// special symbols
export const isValidAnthropicApiKey = (apiKey?: string, anthropicHost?: string | null) => {
  if (!apiKey) return false;

  // [Proxy compatibility] For custom hosts (e.g. api.kiro.cheap), accept any non-empty key
  // Custom proxies may use different key formats than official Anthropic API
  if (anthropicHost) return apiKey.length > 0;

  // For official Anthropic API, validate standard key format (sk-ant-... with length ≥39)
  return apiKey.startsWith('sk-') ? apiKey.length >= 39 : apiKey.length > 1;
};

interface DAnthropicServiceSettings {
  anthropicKey: string;
  anthropicHost: string;
  csf?: boolean;
  heliconeKey: string;
}

export const ModelVendorAnthropic: IModelVendor<DAnthropicServiceSettings, AnthropicAccessSchema> = {
  id: 'anthropic',
  name: 'Anthropic',
  displayRank: 12,
  displayGroup: 'popular',
  location: 'cloud',
  brandColor: '#cc785c',
  instanceLimit: 1,
  hasServerConfigKey: 'hasLlmAnthropic',

  /// client-side-fetch ///
  csfAvailable: _csfAnthropicAvailable,

  // functions
  getTransportAccess: (partialSetup): AnthropicAccessSchema => ({
    dialect: 'anthropic',
    clientSideFetch: _csfAnthropicAvailable(partialSetup) && !!partialSetup?.csf,
    anthropicKey: partialSetup?.anthropicKey || '',
    anthropicHost: partialSetup?.anthropicHost || null,
    heliconeKey: partialSetup?.heliconeKey || null,
  }),

  // List Models
  rpcUpdateModelsOrThrow: async (access) => await apiAsync.llmAnthropic.listModels.query({ access }),

};

function _csfAnthropicAvailable(s?: Partial<DAnthropicServiceSettings>) {
  return !!s?.anthropicKey;
}
