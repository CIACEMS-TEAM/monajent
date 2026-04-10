---
description: Comprehensive reference documentation for the Groq API, including endpoints, parameters, and examples.
title: API Reference - GroqDocs
---

# Groq API Reference

[Chat](https://console.groq.com/docs/api-reference#chat)

[Create chat completion](https://console.groq.com/docs/api-reference#chat-create)

POSThttps://api.groq.com/openai/v1/chat/completions

Creates a model response for the given chat conversation.

### 

[Request Body](https://console.groq.com/docs/api-reference#chat-create-request-body)

* messagesarrayRequired  
A list of messages comprising the conversation so far.  
### Show possible types
* modelstringRequired  
ID of the model to use. For details on which models are compatible with the Chat API, see available [models](https://console.groq.com/docs/models)
* citation\_optionsstring or nullOptionalDefaults to enabled  
Allowed values: `enabled, disabled`  
Whether to enable citations in the response. When enabled, the model will include citations for information retrieved from provided documents or web searches.
* compound\_customobject or nullOptional  
Custom configuration of models and tools for Compound.  
### Show properties
* disable\_tool\_validationbooleanOptionalDefaults to false  
If set to true, groq will return called tools without validating that the tool is present in request.tools. tool\_choice=required/none will still be enforced, but the request cannot require a specific tool be used.
* documentsarray or nullOptional  
A list of documents to provide context for the conversation. Each document contains text that can be referenced by the model.  
### Show properties
* exclude\_domainsDeprecatedarray or nullOptional  
Deprecated: Use search\_settings.exclude\_domains instead. A list of domains to exclude from the search results when the model uses a web search tool.
* frequency\_penaltynumber or nullOptionalDefaults to 0  
Range: \-2 - 2  
This is not yet supported by any of our models. Number between -2.0 and 2.0\. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
* function\_callDeprecatedstring / object or nullOptional  
Deprecated in favor of `tool_choice`.  
Controls which (if any) function is called by the model.`none` means the model will not call a function and instead generates a message.`auto` means the model can pick between generating a message or calling a function. Specifying a particular function via `{"name": "my_function"}` forces the model to call that function.  
`none` is the default when no functions are present. `auto` is the default if functions are present.  
### Show possible types
* functionsDeprecatedarray or nullOptional  
Deprecated in favor of `tools`.  
A list of functions the model may generate JSON inputs for.  
### Show properties
* include\_domainsDeprecatedarray or nullOptional  
Deprecated: Use search\_settings.include\_domains instead. A list of domains to include in the search results when the model uses a web search tool.
* include\_reasoningboolean or nullOptional  
Whether to include reasoning in the response. If true, the response will include a `reasoning` field. If false, the model's reasoning will not be included in the response. This field is mutually exclusive with `reasoning_format`.
* logit\_biasobject or nullOptional  
This is not yet supported by any of our models. Modify the likelihood of specified tokens appearing in the completion.
* logprobsboolean or nullOptionalDefaults to false  
This is not yet supported by any of our models. Whether to return log probabilities of the output tokens or not. If true, returns the log probabilities of each output token returned in the `content` of `message`.
* max\_completion\_tokensinteger or nullOptional  
The maximum number of tokens that can be generated in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length.
* max\_tokensDeprecatedinteger or nullOptional  
Deprecated in favor of `max_completion_tokens`. The maximum number of tokens that can be generated in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length.
* metadataobject or nullOptional  
This parameter is not currently supported.
* ninteger or nullOptionalDefaults to 1  
Range: 1 - 1  
How many chat completion choices to generate for each input message. Note that the current moment, only n=1 is supported. Other values will result in a 400 response.
* parallel\_tool\_callsboolean or nullOptionalDefaults to true  
Whether to enable parallel function calling during tool use.
* presence\_penaltynumber or nullOptionalDefaults to 0  
Range: \-2 - 2  
This is not yet supported by any of our models. Number between -2.0 and 2.0\. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
* reasoning\_effortstring or nullOptional  
Allowed values: `none, default, low, medium, high`  
qwen3 models support the following values Set to 'none' to disable reasoning. Set to 'default' or null to let Qwen reason.  
openai/gpt-oss-20b and openai/gpt-oss-120b support 'low', 'medium', or 'high'. 'medium' is the default value.
* reasoning\_formatstring or nullOptional  
Allowed values: `hidden, raw, parsed`  
Specifies how to output reasoning tokens This field is mutually exclusive with `include_reasoning`.
* response\_formatobject / object / object or nullOptional  
An object specifying the format that the model must output. Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured Outputs which ensures the model will match your supplied JSON schema. `json_schema` response format is only available on [supported models](https://console.groq.com/docs/structured-outputs#supported-models). Setting to `{ "type": "json_object" }` enables the older JSON mode, which ensures the message the model generates is valid JSON. Using `json_schema` is preferred for models that support it.  
### Show possible types
* search\_settingsobject or nullOptional  
Settings for web search functionality when the model uses a web search tool.  
### Show properties
* seedinteger or nullOptional  
If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result. Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.
* service\_tierstring or nullOptional  
Allowed values: `auto, on_demand, flex, performance, null`  
The service tier to use for the request. Defaults to `on_demand`.  
   * `auto` will automatically select the highest tier available within the rate limits of your organization.  
   * `flex` uses the flex tier, which will succeed or fail quickly.
* stopstring / array or nullOptional  
Up to 4 sequences where the API will stop generating further tokens. The returned text will not contain the stop sequence.  
### Show possible types
* storeboolean or nullOptional  
This parameter is not currently supported.
* streamboolean or nullOptionalDefaults to false  
If set, partial message deltas will be sent. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent%5Fevents/Using%5Fserver-sent%5Fevents#Event%5Fstream%5Fformat) as they become available, with the stream terminated by a `data: [DONE]` message. [Example code](https://console.groq.com/docs/text-chat#streaming-a-chat-completion).
* stream\_optionsobject or nullOptional  
Options for streaming response. Only set this when you set `stream: true`.  
### Show properties
* temperaturenumber or nullOptionalDefaults to 1  
Range: 0 - 2  
What sampling temperature to use, between 0 and 2\. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. We generally recommend altering this or top\_p but not both.
* tool\_choicestring / object or nullOptional  
Controls which (if any) tool is called by the model.`none` means the model will not call any tool and instead generates a message.`auto` means the model can pick between generating a message or calling one or more tools.`required` means the model must call one or more tools. Specifying a particular tool via `{"type": "function", "function": {"name": "my_function"}}` forces the model to call that tool.  
`none` is the default when no tools are present. `auto` is the default if tools are present.  
### Show possible types
* toolsarray or nullOptional  
A list of tools the model may call. Currently, only functions are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for. A max of 128 functions are supported.  
### Show properties
* top\_logprobsinteger or nullOptional  
Range: 0 - 20  
This is not yet supported by any of our models. An integer between 0 and 20 specifying the number of most likely tokens to return at each token position, each with an associated log probability. `logprobs` must be set to `true` if this parameter is used.
* top\_pnumber or nullOptionalDefaults to 1  
Range: 0 - 1  
An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top\_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both.
* userstring or nullOptional  
A unique identifier representing your end-user, which can help us monitor and detect abuse.

### 

[Response Object](https://console.groq.com/docs/api-reference#chat-create-returns)

* choicesarray  
A list of chat completion choices. Can be more than one if `n` is greater than 1.  
### Show properties
* createdinteger  
The Unix timestamp (in seconds) of when the chat completion was created.
* idstring  
A unique identifier for the chat completion.
* mcp\_list\_toolsarray or null  
List of discovered MCP tools from connected servers.  
### Show properties
* modelstring  
The model used for the chat completion.
* objectstring  
Allowed values: `chat.completion`  
The object type, which is always `chat.completion`.
* service\_tierstring or null  
Allowed values: `auto, on_demand, flex, performance, null`  
The service tier used for the request.
* system\_fingerprintstring  
This fingerprint represents the backend configuration that the model runs with.  
Can be used in conjunction with the `seed` request parameter to understand when backend changes have been made that might impact determinism.
* usageobject  
Usage statistics for the completion request.  
### Show properties
* usage\_breakdownobject  
Usage statistics for compound AI completion requests.  
### Show properties
* x\_groqobject  
Groq-specific metadata for non-streaming chat completion responses.  
### Show properties

curl

```
curl https://api.groq.com/openai/v1/chat/completions -s \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GROQ_API_KEY" \
-d '{
  "model": "llama-3.3-70b-versatile",
  "messages": [{
      "role": "user",
      "content": "Explain the importance of fast language models"
  }]
}'
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
  const completion = await groq.chat.completions
    .create({
      messages: [
        {
          role: "user",
          content: "Explain the importance of fast language models",
        },
      ],
      model: "llama-3.3-70b-versatile",
    })
  console.log(completion.choices[0].message.content);
}

main();
```

```
import os

from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)
```

Example Response

```
{
  "id": "chatcmpl-f51b2cd2-bef7-417e-964e-a08f0b513c22",
  "object": "chat.completion",
  "created": 1730241104,
  "model": "openai/gpt-oss-20b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Fast language models have gained significant attention in recent years due to their ability to process and generate human-like text quickly and efficiently. The importance of fast language models can be understood from their potential applications and benefits:\n\n1. **Real-time Chatbots and Conversational Interfaces**: Fast language models enable the development of chatbots and conversational interfaces that can respond promptly to user queries, making them more engaging and useful.\n2. **Sentiment Analysis and Opinion Mining**: Fast language models can quickly analyze text data to identify sentiments, opinions, and emotions, allowing for improved customer service, market research, and opinion mining.\n3. **Language Translation and Localization**: Fast language models can quickly translate text between languages, facilitating global communication and enabling businesses to reach a broader audience.\n4. **Text Summarization and Generation**: Fast language models can summarize long documents or even generate new text on a given topic, improving information retrieval and processing efficiency.\n5. **Named Entity Recognition and Information Extraction**: Fast language models can rapidly recognize and extract specific entities, such as names, locations, and organizations, from unstructured text data.\n6. **Recommendation Systems**: Fast language models can analyze large amounts of text data to personalize product recommendations, improve customer experience, and increase sales.\n7. **Content Generation for Social Media**: Fast language models can quickly generate engaging content for social media platforms, helping businesses maintain a consistent online presence and increasing their online visibility.\n8. **Sentiment Analysis for Stock Market Analysis**: Fast language models can quickly analyze social media posts, news articles, and other text data to identify sentiment trends, enabling financial analysts to make more informed investment decisions.\n9. **Language Learning and Education**: Fast language models can provide instant feedback and adaptive language learning, making language education more effective and engaging.\n10. **Domain-Specific Knowledge Extraction**: Fast language models can quickly extract relevant information from vast amounts of text data, enabling domain experts to focus on high-level decision-making rather than manual information gathering.\n\nThe benefits of fast language models include:\n\n* **Increased Efficiency**: Fast language models can process large amounts of text data quickly, reducing the time and effort required for tasks such as sentiment analysis, entity recognition, and text summarization.\n* **Improved Accuracy**: Fast language models can analyze and learn from large datasets, leading to more accurate results and more informed decision-making.\n* **Enhanced User Experience**: Fast language models can enable real-time interactions, personalized recommendations, and timely responses, improving the overall user experience.\n* **Cost Savings**: Fast language models can automate many tasks, reducing the need for manual labor and minimizing costs associated with data processing and analysis.\n\nIn summary, fast language models have the potential to transform various industries and applications by providing fast, accurate, and efficient language processing capabilities."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "queue_time": 0.037493756,
    "prompt_tokens": 18,
    "prompt_time": 0.000680594,
    "completion_tokens": 556,
    "completion_time": 0.463333333,
    "total_tokens": 574,
    "total_time": 0.464013927
  },
  "system_fingerprint": "fp_179b0f92c9",
  "x_groq": { "id": "req_01jbd6g2qdfw2adyrt2az8hz4w" }
}
```

[Responses (beta)](https://console.groq.com/docs/api-reference#responses)

[Create response](https://console.groq.com/docs/api-reference#responses-create)

POSThttps://api.groq.com/openai/v1/responses

Creates a model response for the given input.

### 

[Request Body](https://console.groq.com/docs/api-reference#responses-create-request-body)

* inputstring / arrayRequired  
Text input to the model, used to generate a response.  
### Show possible types
* modelstringRequired  
ID of the model to use. For details on which models are compatible with the Responses API, see available [models](https://console.groq.com/docs/models)
* instructionsstring or nullOptional  
Inserts a system (or developer) message as the first item in the model's context.
* max\_output\_tokensinteger or nullOptional  
An upper bound for the number of tokens that can be generated for a response, including visible output tokens and reasoning tokens.
* metadataobject or nullOptional  
Custom key-value pairs for storing additional information. Maximum of 16 pairs.
* parallel\_tool\_callsboolean or nullOptionalDefaults to true  
Enable parallel execution of multiple tool calls.
* reasoningobject or nullOptional  
Configuration for reasoning capabilities when using [models that support reasoning](https://console.groq.com/docs/reasoning).  
### Show properties
* service\_tierstring or nullOptionalDefaults to auto  
Allowed values: `auto, default, flex`  
Specifies the latency tier to use for processing the request.
* storeboolean or nullOptionalDefaults to false  
Response storage flag. Note: Currently only supports false or null values.
* streamboolean or nullOptionalDefaults to false  
Enable streaming mode to receive response data as server-sent events.
* temperaturenumber or nullOptionalDefaults to 1  
Range: 0 - 2  
Controls randomness in the response generation. Range: 0 to 2\. Lower values produce more deterministic outputs, higher values increase variety and creativity.
* textobjectOptional  
Response format configuration. Supports plain text or structured JSON output.  
### Show properties
* tool\_choicestring / object or nullOptional  
Controls which (if any) tool is called by the model.`none` means the model will not call any tool and instead generates a message.`auto` means the model can pick between generating a message or calling one or more tools.`required` means the model must call one or more tools. Specifying a particular tool via `{"type": "function", "function": {"name": "my_function"}}` forces the model to call that tool.  
`none` is the default when no tools are present. `auto` is the default if tools are present.  
### Show possible types
* toolsarray or nullOptional  
List of tools available to the model. Currently supports function definitions only. Maximum of 128 functions.  
### Show properties
* top\_pnumber or nullOptionalDefaults to 1  
Range: 0 - 1  
Nucleus sampling parameter that controls the cumulative probability cutoff. Range: 0 to 1\. A value of 0.1 restricts sampling to tokens within the top 10% probability mass.
* truncationstring or nullOptionalDefaults to disabled  
Allowed values: `auto, disabled`  
Context truncation strategy. Supported values: `auto` or `disabled`.
* userstringOptional  
Optional identifier for tracking end-user requests. Useful for usage monitoring and compliance.

### 

[Response Object](https://console.groq.com/docs/api-reference#responses-create-returns)

* backgroundboolean  
Whether the response was generated in the background.
* created\_atinteger  
The Unix timestamp (in seconds) of when the response was created.
* errorobject or null  
An error object if the response failed.  
### Show properties
* idstring  
A unique identifier for the response.
* incomplete\_detailsobject or null  
Details about why the response is incomplete.  
### Show properties
* instructionsstring or null  
The system instructions used for the response.
* max\_output\_tokensinteger or null  
The maximum number of tokens configured for the response.
* max\_tool\_callsinteger or null  
The maximum number of tool calls allowed.
* metadataobject or null  
Metadata attached to the response.
* modelstring  
The model used for the response.
* objectstring  
Allowed values: `response`  
The object type, which is always `response`.
* outputarray  
An array of content items generated by the model.  
### Show possible types
* parallel\_tool\_callsboolean  
Whether the model can run tool calls in parallel.
* previous\_response\_idstring or null  
Not supported. Always null.
* reasoningobject or null  
Configuration options for [models that support reasoning](https://console.groq.com/docs/reasoning).  
### Show properties
* service\_tierstring  
Allowed values: `auto, default, flex`  
The service tier used for processing.
* statusstring  
Allowed values: `completed, failed, in_progress, incomplete`  
The status of the response generation. One of `completed`, `failed`, `in_progress`, or `incomplete`.
* storeboolean  
Whether the response was stored.
* temperaturenumber  
The sampling temperature used.
* textobject  
Text format configuration used for the response.  
### Show properties
* tool\_choicestring / object or null  
Controls which (if any) tool is called by the model.`none` means the model will not call any tool and instead generates a message.`auto` means the model can pick between generating a message or calling one or more tools.`required` means the model must call one or more tools. Specifying a particular tool via `{"type": "function", "function": {"name": "my_function"}}` forces the model to call that tool.  
`none` is the default when no tools are present. `auto` is the default if tools are present.  
### Show possible types
* toolsarray  
The tools that were available to the model.  
### Show properties
* top\_logprobsinteger  
The number of top log probabilities returned.
* top\_pnumber  
The nucleus sampling parameter used.
* truncationstring  
Allowed values: `auto, disabled`  
The truncation strategy used.
* usageobject  
Usage statistics for the response request.  
### Show properties
* userstring or null  
The user identifier.

Example request

```
curl https://api.groq.com/openai/v1/responses -s \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $GROQ_API_KEY" \
-d '{
  "model": "openai/gpt-oss-120b",
  "input": "Tell me a three sentence bedtime story about a unicorn."
}'
```

Example Response

```
{
  "id": "resp_01k1x6w9ane6d8rfxm05cb45yk",
  "object": "response",
  "status": "completed",
  "created_at": 1754400695,
  "output": [
    {
      "type": "message",
      "id": "msg_01k1x6w9ane6eb0650crhawwyy",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "When the stars blinked awake, Luna the unicorn curled her mane and whispered wishes to the sleeping pine trees. She galloped through a field of moonlit daisies, gathering dew like tiny silver pearls. With a gentle sigh, she tucked her hooves beneath a silver cloud so the world slept softly, dreaming of her gentle hooves until the morning.",
          "annotations": []
        }
      ]
    }
  ],
  "previous_response_id": null,
  "model": "llama-3.3-70b-versatile",
  "reasoning": {
    "effort": null,
    "summary": null
  },
  "max_output_tokens": null,
  "instructions": null,
  "text": {
    "format": {
      "type": "text"
    }
  },
  "tools": [],
  "tool_choice": "auto",
  "truncation": "disabled",
  "metadata": {},
  "temperature": 1,
  "top_p": 1,
  "user": null,
  "service_tier": "default",
  "error": null,
  "incomplete_details": null,
  "usage": {
    "input_tokens": 82,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 266,
    "output_tokens_details": {
      "reasoning_tokens": 0
    },
    "total_tokens": 348
  },
  "parallel_tool_calls": true,
  "store": false
}
```

[Audio](https://console.groq.com/docs/api-reference#audio)

[Create transcription](https://console.groq.com/docs/api-reference#audio-transcription)

POSThttps://api.groq.com/openai/v1/audio/transcriptions

Transcribes audio into the input language.

### 

[Request Body](https://console.groq.com/docs/api-reference#audio-transcription-request-body)

* modelstringRequired  
ID of the model to use. `whisper-large-v3` and `whisper-large-v3-turbo` are currently available.
* filestringOptional  
The audio file object (not file name) to transcribe, in one of these formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, or webm. Either a file or a URL must be provided. Note that the file field is not supported in Batch API requests.
* languagestringOptional  
The language of the input audio. Supplying the input language in [ISO-639-1](https://en.wikipedia.org/wiki/List%5Fof%5FISO%5F639-1%5Fcodes) format will improve accuracy and latency.
* promptstringOptional  
An optional text to guide the model's style or continue a previous audio segment. The [prompt](https://console.groq.com/docs/speech-text) should match the audio language.
* response\_formatstringOptionalDefaults to json  
Allowed values: `json, text, verbose_json`  
The format of the transcript output, in one of these options: `json`, `text`, or `verbose_json`.
* temperaturenumberOptionalDefaults to 0  
The sampling temperature, between 0 and 1\. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log%5Fprobability) to automatically increase the temperature until certain thresholds are hit.
* timestamp\_granularities\[\]arrayOptionalDefaults to segment  
The timestamp granularities to populate for this transcription. `response_format` must be set `verbose_json` to use timestamp granularities. Either or both of these options are supported: `word`, or `segment`. Note: There is no additional latency for segment timestamps, but generating word timestamps incurs additional latency.
* urlstringOptional  
The audio URL to translate/transcribe (supports Base64URL). Either a file or a URL must be provided. For Batch API requests, the URL field is required since the file field is not supported.

### 

[Response Object](https://console.groq.com/docs/api-reference#audio-transcription-returns)

* textstring  
The transcribed text.

curl

```
curl https://api.groq.com/openai/v1/audio/transcriptions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@./sample_audio.m4a" \
  -F model="whisper-large-v3"
```

```
import fs from "fs";
import Groq from "groq-sdk";

const groq = new Groq();
async function main() {
  const transcription = await groq.audio.transcriptions.create({
    file: fs.createReadStream("sample_audio.m4a"),
    model: "whisper-large-v3",
    prompt: "Specify context or spelling", // Optional
    response_format: "json", // Optional
    language: "en", // Optional
    temperature: 0.0, // Optional
  });
  console.log(transcription.text);
}
main();
```

```
import os
from groq import Groq

client = Groq()
filename = os.path.dirname(__file__) + "/sample_audio.m4a"

with open(filename, "rb") as file:
    transcription = client.audio.transcriptions.create(
      file=(filename, file.read()),
      model="whisper-large-v3",
      prompt="Specify context or spelling",  # Optional
      response_format="json",  # Optional
      language="en",  # Optional
      temperature=0.0  # Optional
    )
    print(transcription.text)
```

Example Response

```
{
  "text": "Your transcribed text appears here...",
  "x_groq": {
    "id": "req_unique_id"
  }
}
```

[Create translation](https://console.groq.com/docs/api-reference#audio-translation)

POSThttps://api.groq.com/openai/v1/audio/translations

Translates audio into English.

### 

[Request Body](https://console.groq.com/docs/api-reference#audio-translation-request-body)

* modelstringRequired  
ID of the model to use. `whisper-large-v3` and `whisper-large-v3-turbo` are currently available.
* filestringOptional  
The audio file object (not file name) translate, in one of these formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, or webm.
* promptstringOptional  
An optional text to guide the model's style or continue a previous audio segment. The [prompt](https://console.groq.com/docs/guides/speech-to-text/prompting) should be in English.
* response\_formatstringOptionalDefaults to json  
Allowed values: `json, text, verbose_json`  
The format of the transcript output, in one of these options: `json`, `text`, or `verbose_json`.
* temperaturenumberOptionalDefaults to 0  
The sampling temperature, between 0 and 1\. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. If set to 0, the model will use [log probability](https://en.wikipedia.org/wiki/Log%5Fprobability) to automatically increase the temperature until certain thresholds are hit.
* urlstringOptional  
The audio URL to translate/transcribe (supports Base64URL). Either file or url must be provided. When using the Batch API only url is supported.

### 

[Response Object](https://console.groq.com/docs/api-reference#audio-translation-returns)

* textstring

curl

```
curl https://api.groq.com/openai/v1/audio/translations \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@./sample_audio.m4a" \
  -F model="whisper-large-v3"
```

```
// Default
import fs from "fs";
import Groq from "groq-sdk";

const groq = new Groq();
async function main() {
  const translation = await groq.audio.translations.create({
    file: fs.createReadStream("sample_audio.m4a"),
    model: "whisper-large-v3",
    prompt: "Specify context or spelling", // Optional
    response_format: "json", // Optional
    temperature: 0.0, // Optional
  });
  console.log(translation.text);
}
main();
```

```
# Default
import os
from groq import Groq

client = Groq()
filename = os.path.dirname(__file__) + "/sample_audio.m4a"

with open(filename, "rb") as file:
    translation = client.audio.translations.create(
      file=(filename, file.read()),
      model="whisper-large-v3",
      prompt="Specify context or spelling",  # Optional
      response_format="json",  # Optional
      temperature=0.0  # Optional
    )
    print(translation.text)
```

Example Response

```
{
  "text": "Your translated text appears here...",
  "x_groq": {
    "id": "req_unique_id"
  }
}
```

[Create speech](https://console.groq.com/docs/api-reference#audio-speech)

POSThttps://api.groq.com/openai/v1/audio/speech

Generates audio from the input text.

### 

[Request Body](https://console.groq.com/docs/api-reference#audio-speech-request-body)

* inputstringRequired  
The text to generate audio for.
* modelstringRequired  
One of the [available TTS models](https://console.groq.com/docs/text-to-speech).
* voicestringRequired  
The voice to use when generating the audio. List of voices can be found [here](https://console.groq.com/docs/text-to-speech).
* response\_formatstringOptionalDefaults to mp3  
Allowed values: `flac, mp3, mulaw, ogg, wav`  
The format of the generated audio. Supported formats are `flac, mp3, mulaw, ogg, wav`.
* sample\_rateintegerOptionalDefaults to 48000  
Allowed values: `8000, 16000, 22050, 24000, 32000, 44100, 48000`  
The sample rate for generated audio
* speednumberOptionalDefaults to 1  
Range: 0.5 - 5  
The speed of the generated audio.

### 

[Returns](https://console.groq.com/docs/api-reference#audio-speech-returns)

Returns an audio file in `wav` format.

curl

```
curl https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "playai-tts",
    "input": "I love building and shipping new features for our users!",
    "voice": "Fritz-PlayAI",
    "response_format": "wav"
  }'
```

```
import fs from "fs";
import path from "path";
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY
});

const speechFilePath = "speech.wav";
const model = "playai-tts";
const voice = "Fritz-PlayAI";
const text = "I love building and shipping new features for our users!";
const responseFormat = "wav";

async function main() {
  const response = await groq.audio.speech.create({
    model: model,
    voice: voice,
    input: text,
    response_format: responseFormat
  });

  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.promises.writeFile(speechFilePath, buffer);
}

main();
```

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "speech.wav"
model = "playai-tts"
voice = "Fritz-PlayAI"
text = "I love building and shipping new features for our users!"
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)
```

Example Response

```
"string"
```

[Models](https://console.groq.com/docs/api-reference#models)

[List models](https://console.groq.com/docs/api-reference#models-list)

GEThttps://api.groq.com/openai/v1/models

List all available [models](https://console.groq.com/docs/models).

### 

[Response Object](https://console.groq.com/docs/api-reference#models-list-returns)

* dataarray  
### Show properties
* objectstring  
Allowed values: `list`

curl

```
curl https://api.groq.com/openai/v1/models \
-H "Authorization: Bearer $GROQ_API_KEY"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
  const models = await groq.models.list();
  console.log(models);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

models = client.models.list()

print(models)
```

Example Response

```
{
  "object": "list",
  "data": [
    {
      "id": "gemma2-9b-it",
      "object": "model",
      "created": 1693721698,
      "owned_by": "Google",
      "active": true,
      "context_window": 8192,
      "public_apps": null
    },
    {
      "id": "llama3-8b-8192",
      "object": "model",
      "created": 1693721698,
      "owned_by": "Meta",
      "active": true,
      "context_window": 8192,
      "public_apps": null
    },
    {
      "id": "llama3-70b-8192",
      "object": "model",
      "created": 1693721698,
      "owned_by": "Meta",
      "active": true,
      "context_window": 8192,
      "public_apps": null
    },
    {
      "id": "whisper-large-v3-turbo",
      "object": "model",
      "created": 1728413088,
      "owned_by": "OpenAI",
      "active": true,
      "context_window": 448,
      "public_apps": null
    },
    {
      "id": "whisper-large-v3",
      "object": "model",
      "created": 1693721698,
      "owned_by": "OpenAI",
      "active": true,
      "context_window": 448,
      "public_apps": null
    },
    {
      "id": "llama-guard-3-8b",
      "object": "model",
      "created": 1693721698,
      "owned_by": "Meta",
      "active": true,
      "context_window": 8192,
      "public_apps": null
    },
    {
      "id": "distil-whisper-large-v3-en",
      "object": "model",
      "created": 1693721698,
      "owned_by": "Hugging Face",
      "active": true,
      "context_window": 448,
      "public_apps": null
    },
    {
      "id": "llama-3.1-8b-instant",
      "object": "model",
      "created": 1693721698,
      "owned_by": "Meta",
      "active": true,
      "context_window": 131072,
      "public_apps": null
    }
  ]
}
```

[Retrieve model](https://console.groq.com/docs/api-reference#models-retrieve)

GEThttps://api.groq.com/openai/v1/models/{model}

Get detailed information about a [model](https://console.groq.com/docs/models).

### 

[Response Object](https://console.groq.com/docs/api-reference#models-retrieve-returns)

* createdinteger  
The Unix timestamp (in seconds) when the model was created.
* idstring  
The model identifier, which can be referenced in the API endpoints.
* objectstring  
Allowed values: `model`  
The object type, which is always "model".
* owned\_bystring  
The organization that owns the model.

curl

```
curl https://api.groq.com/openai/v1/models/llama-3.3-70b-versatile \
-H "Authorization: Bearer $GROQ_API_KEY"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
  const model = await groq.models.retrieve("llama-3.3-70b-versatile");
  console.log(model);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

model = client.models.retrieve("llama-3.3-70b-versatile")

print(model)
```

Example Response

```
{
  "id": "llama3-8b-8192",
  "object": "model",
  "created": 1693721698,
  "owned_by": "Meta",
  "active": true,
  "context_window": 8192,
  "public_apps": null,
  "max_completion_tokens": 8192
}
```

[Batches](https://console.groq.com/docs/api-reference#batches)

[Create batch](https://console.groq.com/docs/api-reference#batches-create)

POSThttps://api.groq.com/openai/v1/batches

Creates and executes a batch from an uploaded file of requests. [Learn more](https://console.groq.com/docs/batch).

### 

[Request Body](https://console.groq.com/docs/api-reference#batches-create-request-body)

* completion\_windowstringRequired  
The time frame within which the batch should be processed. Durations from `24h` to `7d` are supported.
* endpointstringRequired  
Allowed values: `/v1/chat/completions`  
The endpoint to be used for all requests in the batch. Currently `/v1/chat/completions` is supported.
* input\_file\_idstringRequired  
The ID of an uploaded file that contains requests for the new batch.  
See [upload file](https://console.groq.com/docs/api-reference#files-upload) for how to upload a file.  
Your input file must be formatted as a [JSONL file](https://console.groq.com/docs/batch), and must be uploaded with the purpose `batch`. The file can be up to 100 MB in size.
* metadataobject or nullOptional  
Optional custom metadata for the batch.

### 

[Response Object](https://console.groq.com/docs/api-reference#batches-create-returns)

* cancelled\_atinteger  
The Unix timestamp (in seconds) for when the batch was cancelled.
* cancelling\_atinteger  
The Unix timestamp (in seconds) for when the batch started cancelling.
* completed\_atinteger  
The Unix timestamp (in seconds) for when the batch was completed.
* completion\_windowstring  
The time frame within which the batch should be processed.
* created\_atinteger  
The Unix timestamp (in seconds) for when the batch was created.
* endpointstring  
The API endpoint used by the batch.
* error\_file\_idstring  
The ID of the file containing the outputs of requests with errors.
* errorsobject  
### Show properties
* expired\_atinteger  
The Unix timestamp (in seconds) for when the batch expired.
* expires\_atinteger  
The Unix timestamp (in seconds) for when the batch will expire.
* failed\_atinteger  
The Unix timestamp (in seconds) for when the batch failed.
* finalizing\_atinteger  
The Unix timestamp (in seconds) for when the batch started finalizing.
* idstring
* in\_progress\_atinteger  
The Unix timestamp (in seconds) for when the batch started processing.
* input\_file\_idstring  
The ID of the input file for the batch.
* metadataobject or null  
Set of key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format.
* objectstring  
Allowed values: `batch`  
The object type, which is always `batch`.
* output\_file\_idstring  
The ID of the file containing the outputs of successfully executed requests.
* request\_countsobject  
The request counts for different statuses within the batch.  
### Show properties
* statusstring  
Allowed values: `validating, failed, in_progress, finalizing, completed, expired, cancelling, cancelled`  
The current status of the batch.

curl

```
curl https://api.groq.com/openai/v1/batches \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
    "endpoint": "/v1/chat/completions",
    "completion_window": "24h"
  }'
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const batch = await client.batches.create({
    completion_window: "24h",
    endpoint: "/v1/chat/completions",
    input_file_id: "file_01jh6x76wtemjr74t1fh0faj5t",
  });
  console.log(batch.id);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
batch = client.batches.create(
    completion_window="24h",
    endpoint="/v1/chat/completions",
    input_file_id="file_01jh6x76wtemjr74t1fh0faj5t",
)
print(batch.id)
```

Example Response

```
{
  "id": "batch_01jh6xa7reempvjyh6n3yst2zw",
  "object": "batch",
  "endpoint": "/v1/chat/completions",
  "errors": null,
  "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
  "completion_window": "24h",
  "status": "validating",
  "output_file_id": null,
  "error_file_id": null,
  "finalizing_at": null,
  "failed_at": null,
  "expired_at": null,
  "cancelled_at": null,
  "request_counts": {
    "total": 0,
    "completed": 0,
    "failed": 0
  },
  "metadata": null,
  "created_at": 1736472600,
  "expires_at": 1736559000,
  "cancelling_at": null,
  "completed_at": null,
  "in_progress_at": null
}
```

[Retrieve batch](https://console.groq.com/docs/api-reference#batches-retrieve)

GEThttps://api.groq.com/openai/v1/batches/{batch\_id}

Retrieves a batch.

### 

[Response Object](https://console.groq.com/docs/api-reference#batches-retrieve-returns)

* cancelled\_atinteger  
The Unix timestamp (in seconds) for when the batch was cancelled.
* cancelling\_atinteger  
The Unix timestamp (in seconds) for when the batch started cancelling.
* completed\_atinteger  
The Unix timestamp (in seconds) for when the batch was completed.
* completion\_windowstring  
The time frame within which the batch should be processed.
* created\_atinteger  
The Unix timestamp (in seconds) for when the batch was created.
* endpointstring  
The API endpoint used by the batch.
* error\_file\_idstring  
The ID of the file containing the outputs of requests with errors.
* errorsobject  
### Show properties
* expired\_atinteger  
The Unix timestamp (in seconds) for when the batch expired.
* expires\_atinteger  
The Unix timestamp (in seconds) for when the batch will expire.
* failed\_atinteger  
The Unix timestamp (in seconds) for when the batch failed.
* finalizing\_atinteger  
The Unix timestamp (in seconds) for when the batch started finalizing.
* idstring
* in\_progress\_atinteger  
The Unix timestamp (in seconds) for when the batch started processing.
* input\_file\_idstring  
The ID of the input file for the batch.
* metadataobject or null  
Set of key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format.
* objectstring  
Allowed values: `batch`  
The object type, which is always `batch`.
* output\_file\_idstring  
The ID of the file containing the outputs of successfully executed requests.
* request\_countsobject  
The request counts for different statuses within the batch.  
### Show properties
* statusstring  
Allowed values: `validating, failed, in_progress, finalizing, completed, expired, cancelling, cancelled`  
The current status of the batch.

curl

```
curl https://api.groq.com/openai/v1/batches/batch_01jh6xa7reempvjyh6n3yst2zw \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const batch = await client.batches.retrieve("batch_01jh6xa7reempvjyh6n3yst2zw");
  console.log(batch.id);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
batch = client.batches.retrieve(
    "batch_01jh6xa7reempvjyh6n3yst2zw",
)
print(batch.id)
```

Example Response

```
{
  "id": "batch_01jh6xa7reempvjyh6n3yst2zw",
  "object": "batch",
  "endpoint": "/v1/chat/completions",
  "errors": null,
  "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
  "completion_window": "24h",
  "status": "validating",
  "output_file_id": null,
  "error_file_id": null,
  "finalizing_at": null,
  "failed_at": null,
  "expired_at": null,
  "cancelled_at": null,
  "request_counts": {
    "total": 0,
    "completed": 0,
    "failed": 0
  },
  "metadata": null,
  "created_at": 1736472600,
  "expires_at": 1736559000,
  "cancelling_at": null,
  "completed_at": null,
  "in_progress_at": null
}
```

[List batches](https://console.groq.com/docs/api-reference#batches-list)

GEThttps://api.groq.com/openai/v1/batches

List your organization's batches.

### 

[Response Object](https://console.groq.com/docs/api-reference#batches-list-returns)

* dataarray  
### Show properties
* objectstring  
Allowed values: `list`

curl

```
curl https://api.groq.com/openai/v1/batches \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const batchList = await client.batches.list();
  console.log(batchList.data);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
batch_list = client.batches.list()
print(batch_list.data)
```

Example Response

```
{
  "object": "list",
  "data": [
    {
      "id": "batch_01jh6xa7reempvjyh6n3yst2zw",
      "object": "batch",
      "endpoint": "/v1/chat/completions",
      "errors": null,
      "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
      "completion_window": "24h",
      "status": "validating",
      "output_file_id": null,
      "error_file_id": null,
      "finalizing_at": null,
      "failed_at": null,
      "expired_at": null,
      "cancelled_at": null,
      "request_counts": {
        "total": 0,
        "completed": 0,
        "failed": 0
      },
      "metadata": null,
      "created_at": 1736472600,
      "expires_at": 1736559000,
      "cancelling_at": null,
      "completed_at": null,
      "in_progress_at": null
    }
  ]
}
```

[Cancel batch](https://console.groq.com/docs/api-reference#batches-cancel)

POSThttps://api.groq.com/openai/v1/batches/{batch\_id}/cancel

Cancels a batch.

### 

[Response Object](https://console.groq.com/docs/api-reference#batches-cancel-returns)

* cancelled\_atinteger  
The Unix timestamp (in seconds) for when the batch was cancelled.
* cancelling\_atinteger  
The Unix timestamp (in seconds) for when the batch started cancelling.
* completed\_atinteger  
The Unix timestamp (in seconds) for when the batch was completed.
* completion\_windowstring  
The time frame within which the batch should be processed.
* created\_atinteger  
The Unix timestamp (in seconds) for when the batch was created.
* endpointstring  
The API endpoint used by the batch.
* error\_file\_idstring  
The ID of the file containing the outputs of requests with errors.
* errorsobject  
### Show properties
* expired\_atinteger  
The Unix timestamp (in seconds) for when the batch expired.
* expires\_atinteger  
The Unix timestamp (in seconds) for when the batch will expire.
* failed\_atinteger  
The Unix timestamp (in seconds) for when the batch failed.
* finalizing\_atinteger  
The Unix timestamp (in seconds) for when the batch started finalizing.
* idstring
* in\_progress\_atinteger  
The Unix timestamp (in seconds) for when the batch started processing.
* input\_file\_idstring  
The ID of the input file for the batch.
* metadataobject or null  
Set of key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format.
* objectstring  
Allowed values: `batch`  
The object type, which is always `batch`.
* output\_file\_idstring  
The ID of the file containing the outputs of successfully executed requests.
* request\_countsobject  
The request counts for different statuses within the batch.  
### Show properties
* statusstring  
Allowed values: `validating, failed, in_progress, finalizing, completed, expired, cancelling, cancelled`  
The current status of the batch.

curl

```
curl -X POST https://api.groq.com/openai/v1/batches/batch_01jh6xa7reempvjyh6n3yst2zw/cancel \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const batch = await client.batches.cancel("batch_01jh6xa7reempvjyh6n3yst2zw");
  console.log(batch.id);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
batch = client.batches.cancel(
    "batch_01jh6xa7reempvjyh6n3yst2zw",
)
print(batch.id)
```

Example Response

```
{
  "id": "batch_01jh6xa7reempvjyh6n3yst2zw",
  "object": "batch",
  "endpoint": "/v1/chat/completions",
  "errors": null,
  "input_file_id": "file_01jh6x76wtemjr74t1fh0faj5t",
  "completion_window": "24h",
  "status": "cancelling",
  "output_file_id": null,
  "error_file_id": null,
  "finalizing_at": null,
  "failed_at": null,
  "expired_at": null,
  "cancelled_at": null,
  "request_counts": {
    "total": 0,
    "completed": 0,
    "failed": 0
  },
  "metadata": null,
  "created_at": 1736472600,
  "expires_at": 1736559000,
  "cancelling_at": null,
  "completed_at": null,
  "in_progress_at": null
}
```

[Files](https://console.groq.com/docs/api-reference#files)

[Upload file](https://console.groq.com/docs/api-reference#files-upload)

POSThttps://api.groq.com/openai/v1/files

Upload a file that can be used across various endpoints.

The Batch API only supports `.jsonl` files up to 100 MB in size. The input also has a specific required [format](https://console.groq.com/docs/batch).

Please contact us if you need to increase these storage limits.

### 

[Request Body](https://console.groq.com/docs/api-reference#files-upload-request-body)

* filestringRequired  
The File object (not file name) to be uploaded.
* purposestringRequired  
Allowed values: `batch`  
The intended purpose of the uploaded file. Use "batch" for [Batch API](https://console.groq.com/docs/api-reference#batches).

### 

[Response Object](https://console.groq.com/docs/api-reference#files-upload-returns)

* bytesinteger  
The size of the file, in bytes.
* created\_atinteger  
The Unix timestamp (in seconds) for when the file was created.
* filenamestring  
The name of the file.
* idstring  
The file identifier, which can be referenced in the API endpoints.
* objectstring  
Allowed values: `file`  
The object type, which is always `file`.
* purposestring  
Allowed values: `batch, batch_output`  
The intended purpose of the file. Supported values are `batch`, and `batch_output`.

curl

```
curl https://api.groq.com/openai/v1/files \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -F purpose="batch" \
  -F "file=@batch_file.jsonl"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

const fileContent = '{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Explain the importance of fast language models"}]}}\n';

async function main() {
  const blob = new Blob([fileContent]);
  const file = new File([blob], 'batch.jsonl');

  const createdFile = await client.files.create({ file: file, purpose: 'batch' });
  console.log(createdFile.id);
}

main();
```

```
import os
import requests # pip install requests first!

def upload_file_to_groq(api_key, file_path):
    url = "https://api.groq.com/openai/v1/files"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # Prepare the file and form data
    files = {
        "file": ("batch_file.jsonl", open(file_path, "rb"))
    }

    data = {
        "purpose": "batch"
    }

    # Make the POST request
    response = requests.post(url, headers=headers, files=files, data=data)

    return response.json()

# Usage example
api_key = os.environ.get("GROQ_API_KEY")
file_path = "batch_file.jsonl"  # Path to your JSONL file

try:
    result = upload_file_to_groq(api_key, file_path)
    print(result)
except Exception as e:
    print(f"Error: {e}")
```

Example Response

```
{
  "id": "file_01jh6x76wtemjr74t1fh0faj5t",
  "object": "file",
  "bytes": 966,
  "created_at": 1736472501,
  "filename": "batch_file.jsonl",
  "purpose": "batch"
}
```

[List files](https://console.groq.com/docs/api-reference#files-list)

GEThttps://api.groq.com/openai/v1/files

Returns a list of files.

### 

[Response Object](https://console.groq.com/docs/api-reference#files-list-returns)

* dataarray  
### Show properties
* objectstring  
Allowed values: `list`

curl

```
curl https://api.groq.com/openai/v1/files \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const fileList = await client.files.list();
  console.log(fileList.data);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
file_list = client.files.list()
print(file_list.data)
```

Example Response

```
{
  "object": "list",
  "data": [
    {
      "id": "file_01jh6x76wtemjr74t1fh0faj5t",
      "object": "file",
      "bytes": 966,
      "created_at": 1736472501,
      "filename": "batch_file.jsonl",
      "purpose": "batch"
    }
  ]
}
```

[Delete file](https://console.groq.com/docs/api-reference#files-delete)

DELETEhttps://api.groq.com/openai/v1/files/{file\_id}

Delete a file.

### 

[Response Object](https://console.groq.com/docs/api-reference#files-delete-returns)

* deletedboolean
* idstring
* objectstring  
Allowed values: `file`

curl

```
curl -X DELETE https://api.groq.com/openai/v1/files/file_01jh6x76wtemjr74t1fh0faj5t \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const fileDelete = await client.files.delete("file_01jh6x76wtemjr74t1fh0faj5t");
  console.log(fileDelete);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
file_delete = client.files.delete(
    "file_01jh6x76wtemjr74t1fh0faj5t",
)
print(file_delete)
```

Example Response

```
{
  "id": "file_01jh6x76wtemjr74t1fh0faj5t",
  "object": "file",
  "deleted": true
}
```

[Retrieve file](https://console.groq.com/docs/api-reference#files-retrieve)

GEThttps://api.groq.com/openai/v1/files/{file\_id}

Returns information about a file.

### 

[Response Object](https://console.groq.com/docs/api-reference#files-retrieve-returns)

* bytesinteger  
The size of the file, in bytes.
* created\_atinteger  
The Unix timestamp (in seconds) for when the file was created.
* filenamestring  
The name of the file.
* idstring  
The file identifier, which can be referenced in the API endpoints.
* objectstring  
Allowed values: `file`  
The object type, which is always `file`.
* purposestring  
Allowed values: `batch, batch_output`  
The intended purpose of the file. Supported values are `batch`, and `batch_output`.

curl

```
curl https://api.groq.com/openai/v1/files/file_01jh6x76wtemjr74t1fh0faj5t \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
    const file = await client.files.info('file_01jh6x76wtemjr74t1fh0faj5t');
    console.log(file);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
file = client.files.info(
    "file_01jh6x76wtemjr74t1fh0faj5t",
)
print(file)
```

Example Response

```
{
  "id": "file_01jh6x76wtemjr74t1fh0faj5t",
  "object": "file",
  "bytes": 966,
  "created_at": 1736472501,
  "filename": "batch_file.jsonl",
  "purpose": "batch"
}
```

[Download file](https://console.groq.com/docs/api-reference#files-download)

GEThttps://api.groq.com/openai/v1/files/{file\_id}/content

Returns the contents of the specified file.

### 

[Returns](https://console.groq.com/docs/api-reference#files-download-returns)

The file content

curl

```
curl https://api.groq.com/openai/v1/files/file_01jh6x76wtemjr74t1fh0faj5t/content \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json"
```

```
import Groq from 'groq-sdk';

const client = new Groq({
  apiKey: process.env['GROQ_API_KEY'], // This is the default and can be omitted
});

async function main() {
    const response = await client.files.content('file_01jh6x76wtemjr74t1fh0faj5t');
    console.log(response);
}

main();
```

```
import os
from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)
response = client.files.content(
    "file_01jh6x76wtemjr74t1fh0faj5t",
)
print(response)
```

Example Response

```
"string"
```

[Fine Tuning](https://console.groq.com/docs/api-reference#fine-tuning)

[List fine tunings](https://console.groq.com/docs/api-reference#fine-tuning-list)

GEThttps://api.groq.com/v1/fine\_tunings

Lists all previously created fine tunings. This endpoint is in closed beta. [Contact us](https://groq.com/contact) for more information.

### 

[Response Object](https://console.groq.com/docs/api-reference#fine-tuning-list-returns)

* dataarray  
### Show properties
* objectstring

curl

```
curl https://api.groq.com/v1/fine_tunings -s \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $GROQ_API_KEY"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
    const fineTunings = await groq.fine_tunings.list();
    console.log(fineTunings);
}

main();
```

```
import os

from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

fine_tunings = client.fine_tunings.list()

print(fine_tunings)
```

Example Response

```
{
    "object": "list",
    "data": [
        {
            "id": "string",
            "name": "string",
            "base_model": "string",
            "type": "string",
            "input_file_id": "string",
            "created_at": 0,
            "fine_tuned_model": "string"
        }
    ]
}
```

[Create fine tuning](https://console.groq.com/docs/api-reference#fine-tuning-create)

POSThttps://api.groq.com/v1/fine\_tunings

Creates a new fine tuning for the already uploaded files This endpoint is in closed beta. [Contact us](https://groq.com/contact) for more information.

### 

[Request Body](https://console.groq.com/docs/api-reference#fine-tuning-create-request-body)

* base\_modelstringOptional  
BaseModel is the model that the fine tune was originally trained on.
* input\_file\_idstringOptional  
InputFileID is the id of the file that was uploaded via the /files api.
* namestringOptional  
Name is the given name to a fine tuned model.
* typestringOptional  
Type is the type of fine tuning format such as "lora".

### 

[Response Object](https://console.groq.com/docs/api-reference#fine-tuning-create-returns)

* dataobject  
### Show properties
* idstring
* objectstring

curl

```
curl https://api.groq.com/v1/fine_tunings -s \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -d '{
        "input_file_id": "<file-id>",
        "name": "test-1",
        "type": "lora",
        "base_model": "llama-3.1-8b-instant"
    }'
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
    const fineTunings = await groq.fine_tunings.create({
        input_file_id: "<file-id>",
        name: "test-1",
        type: "lora",
        base_model: "llama-3.1-8b-instant"
    });
    console.log(fineTunings);
}

main();
```

```
import os

from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

fine_tunings = client.fine_tunings.create(
    input_file_id="<file-id>",
    name="test-1",
    type="lora",
    base_model="llama-3.1-8b-instant"
)

print(fine_tunings)
```

Example Response

```
{
    "id": "string",
    "object": "object",
    "data": {
        "id": "string",
        "name": "string",
        "base_model": "string",
        "type": "string",
        "input_file_id": "string",
        "created_at": 0,
        "fine_tuned_model": "string"
    }
}
```

[Get fine tuning](https://console.groq.com/docs/api-reference#fine-tuning-get)

GEThttps://api.groq.com/v1/fine\_tunings/{id}

Retrieves an existing fine tuning by id This endpoint is in closed beta. [Contact us](https://groq.com/contact) for more information.

### 

[Response Object](https://console.groq.com/docs/api-reference#fine-tuning-get-returns)

* dataobject  
### Show properties
* idstring
* objectstring

curl

```
curl https://api.groq.com/v1/fine_tunings/:id -s \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $GROQ_API_KEY"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
    const fineTuning = await groq.fine_tunings.get({id: "<id>"});
    console.log(fineTuning);
}

main();
```

```
import os

from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

fine_tuning = client.fine_tunings.get(id="<id>")

print(fine_tuning)
```

Example Response

```
{
    "id": "string",
    "object": "object",
    "data": {
        "id": "string",
        "name": "string",
        "base_model": "string",
        "type": "string",
        "input_file_id": "string",
        "created_at": 0,
        "fine_tuned_model": "string"
    }
}
```

[Delete fine tuning](https://console.groq.com/docs/api-reference#fine-tuning-delete)

DELETEhttps://api.groq.com/v1/fine\_tunings/{id}

Deletes an existing fine tuning by id This endpoint is in closed beta. [Contact us](https://groq.com/contact) for more information.

### 

[Response Object](https://console.groq.com/docs/api-reference#fine-tuning-delete-returns)

* deletedboolean
* idstring
* objectstring

curl

```
curl -X DELETE https://api.groq.com/v1/fine_tunings/:id -s \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $GROQ_API_KEY"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

async function main() {
    await groq.fine_tunings.delete({id: "<id>"});
}

main();
```

```
import os

from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

client.fine_tunings.delete(id="<id>")
```

Example Response

```
{
    "id": "string",
    "object": "fine_tuning",
    "deleted": true
}
```



---
description: Explore all available models on GroqCloud.
title: Supported Models - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Supported Models

Explore all available models on GroqCloud.

## [Featured Models and Systems](#featured-models-and-systems)

[![Groq Compound icon](https://console.groq.com/_next/image?url=%2Fgroq-circle.png&w=96&q=75)Groq CompoundGroq Compound is an AI system powered by openly available models that intelligently and selectively uses built-in tools to answer user queries, including web search and code execution.Token Speed\~450 tpsModalitiesCapabilities](/docs/compound/systems/compound)[![OpenAI GPT-OSS 120B icon](https://console.groq.com/_next/static/media/openailogo.523c87a0.svg)OpenAI GPT-OSS 120BGPT-OSS 120B is OpenAI's flagship open-weight language model with 120 billion parameters, built in browser search and code execution, and reasoning capabilities.Token Speed\~500 tpsModalitiesCapabilities](/docs/model/openai/gpt-oss-120b)

## [Production Models](#production-models)

**Note:** Production models are intended for use in your production environments. They meet or exceed our high standards for speed, quality, and reliability. Read more [here](https://console.groq.com/docs/deprecations).

| MODEL ID                                                                                                                                 | SPEED (T/SEC) | PRICE PER 1M TOKENS      | RATE LIMITS (DEVELOPER PLAN) | CONTEXT WINDOW (TOKENS) | MAX COMPLETION TOKENS | MAX FILE SIZE |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------ | ---------------------------- | ----------------------- | --------------------- | ------------- |
| [![Meta](https://console.groq.com/_next/image?url=%2FMeta_logo.png&w=48&q=75)Llama 3.1 8B](/docs/model/llama-3.1-8b-instant)llama-3.1-8b-instant                 | 560           | $0.05 input$0.08 output  | 250K TPM1K RPM               | 131,072                 | 131,072               | \-            |
| [![Meta](https://console.groq.com/_next/image?url=%2FMeta_logo.png&w=48&q=75)Llama 3.3 70B](/docs/model/llama-3.3-70b-versatile)llama-3.3-70b-versatile          | 280           | $0.59 input$0.79 output  | 300K TPM1K RPM               | 131,072                 | 32,768                | \-            |
| [![OpenAI](https://console.groq.com/_next/static/media/openailogo.523c87a0.svg)GPT OSS 120B](/docs/model/openai/gpt-oss-120b)openai/gpt-oss-120b                 | 500           | $0.15 input$0.60 output  | 250K TPM1K RPM               | 131,072                 | 65,536                | \-            |
| [![OpenAI](https://console.groq.com/_next/static/media/openailogo.523c87a0.svg)GPT OSS 20B](/docs/model/openai/gpt-oss-20b)openai/gpt-oss-20b                    | 1000          | $0.075 input$0.30 output | 250K TPM1K RPM               | 131,072                 | 65,536                | \-            |
| [![OpenAI](https://console.groq.com/_next/static/media/openailogo.523c87a0.svg)Whisper](/docs/model/whisper-large-v3)whisper-large-v3                            | \-            | $0.111 per hour          | 200K ASH300 RPM              | \-                      | \-                    | 100 MB        |
| [![OpenAI](https://console.groq.com/_next/static/media/openailogo.523c87a0.svg)Whisper Large V3 Turbo](/docs/model/whisper-large-v3-turbo)whisper-large-v3-turbo | \-            | $0.04 per hour           | 400K ASH400 RPM              | \-                      | \-                    | \-            |

## [Production Systems](#production-systems)

Systems are a collection of models and tools that work together to answer a user query.

  
| MODEL ID                                                                                                                      | SPEED (T/SEC) | PRICE PER 1M TOKENS | RATE LIMITS (DEVELOPER PLAN) | CONTEXT WINDOW (TOKENS) | MAX COMPLETION TOKENS | MAX FILE SIZE |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------- | ---------------------------- | ----------------------- | --------------------- | ------------- |
| [![Groq](https://console.groq.com/_next/image?url=%2Fgroq-circle.png&w=48&q=75)Compound](/docs/compound/systems/compound)groq/compound                | 450           | \-                  | 200K TPM200 RPM              | 131,072                 | 8,192                 | \-            |
| [![Groq](https://console.groq.com/_next/image?url=%2Fgroq-circle.png&w=48&q=75)Compound Mini](/docs/compound/systems/compound-mini)groq/compound-mini | 450           | \-                  | 200K TPM200 RPM              | 131,072                 | 8,192                 | \-            |

  
[Learn More About Agentic ToolingDiscover how to build powerful applications with real-time web search and code execution](https://console.groq.com/docs/agentic-tooling) 

## [Preview Models](#preview-models)

**Note:** Preview models are intended for evaluation purposes only and should not be used in production environments as they may be discontinued at short notice. Read more about deprecations [here](https://console.groq.com/docs/deprecations).

| MODEL ID                                                                                                                                                                    | SPEED (T/SEC) | PRICE PER 1M TOKENS      | RATE LIMITS (DEVELOPER PLAN) | CONTEXT WINDOW (TOKENS) | MAX COMPLETION TOKENS | MAX FILE SIZE |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------ | ---------------------------- | ----------------------- | --------------------- | ------------- |
| [![Canopy Labs](https://console.groq.com/_next/image?url=%2Fcanopylabs.png&w=48&q=75)Canopy Labs Orpheus Arabic Saudi](/docs/model/canopylabs/orpheus-arabic-saudi)canopylabs/orpheus-arabic-saudi  | \-            | $40.00 per 1M characters | 50K TPM250 RPM               | 4,000                   | 50,000                | \-            |
| [![Canopy Labs](https://console.groq.com/_next/image?url=%2Fcanopylabs.png&w=48&q=75)Canopy Labs Orpheus V1 English](/docs/model/canopylabs/orpheus-v1-english)canopylabs/orpheus-v1-english        | \-            | $22.00 per 1M characters | 50K TPM250 RPM               | 4,000                   | 50,000                | \-            |
| [![Meta](https://console.groq.com/_next/image?url=%2FMeta_logo.png&w=48&q=75)Llama 4 Scout 17B 16E](/docs/model/meta-llama/llama-4-scout-17b-16e-instruct)meta-llama/llama-4-scout-17b-16e-instruct | 750           | $0.11 input$0.34 output  | 300K TPM1K RPM               | 131,072                 | 8,192                 | 20 MB         |
| [![Meta](https://console.groq.com/_next/image?url=%2FMeta_logo.png&w=48&q=75)Llama Prompt Guard 2 22M](/docs/model/meta-llama/llama-prompt-guard-2-22m)meta-llama/llama-prompt-guard-2-22m          | \-            | $0.03 input$0.03 output  | 30K TPM100 RPM               | 512                     | 512                   | \-            |
| [![Meta](https://console.groq.com/_next/image?url=%2FMeta_logo.png&w=48&q=75)Prompt Guard 2 86M](/docs/model/meta-llama/llama-prompt-guard-2-86m)meta-llama/llama-prompt-guard-2-86m                | \-            | $0.04 input$0.04 output  | 30K TPM100 RPM               | 512                     | 512                   | \-            |
| [![OpenAI](https://console.groq.com/_next/static/media/openailogo.523c87a0.svg)Safety GPT OSS 20B](/docs/model/openai/gpt-oss-safeguard-20b)openai/gpt-oss-safeguard-20b                            | 1000          | $0.075 input$0.30 output | 150K TPM1K RPM               | 131,072                 | 65,536                | \-            |
| [![Alibaba Cloud](https://console.groq.com/_next/image?url=%2Fqwen_logo.png&w=48&q=75)Qwen3-32B](/docs/model/qwen/qwen3-32b)qwen/qwen3-32b                                                          | 400           | $0.29 input$0.59 output  | 300K TPM1K RPM               | 131,072                 | 40,960                | \-            |

## [Deprecated Models](#deprecated-models)

Deprecated models are models that are no longer supported or will no longer be supported in the future. See our deprecation guidelines and deprecated models [here](https://console.groq.com/docs/deprecations).

## [Get All Available Models](#get-all-available-models)

Hosted models are directly accessible through the GroqCloud Models API endpoint using the model IDs mentioned above. You can use the `https://api.groq.com/openai/v1/models` endpoint to return a JSON list of all active models:

Python

```
curl -X GET "https://api.groq.com/openai/v1/models" \
     -H "Authorization: Bearer $GROQ_API_KEY" \
     -H "Content-Type: application/json"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const getModels = async () => {
  return await groq.models.list();
};

getModels().then((models) => {
  // console.log(models);
});
```

```
import requests
import os

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print(response.json())
```


---
description: Learn how to use OpenAI&#x27;s client libraries with Groq API, including configuration, supported features, and limitations.
title: OpenAI Compatibility - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# OpenAI Compatibility

We designed Groq API to be mostly compatible with OpenAI's client libraries, making it easy to configure your existing applications to run on Groq and try our inference speed.

  
We also have our own [Groq Python and Groq TypeScript libraries](https://console.groq.com/docs/libraries) that we encourage you to use.

## [Configuring OpenAI to Use Groq API](#configuring-openai-to-use-groq-api)

To start using Groq with OpenAI's client libraries, pass your Groq API key to the `api_key` parameter and change the `base_url` to `https://api.groq.com/openai/v1`:

PythonJavaScript

Python

```
import os
import openai

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)
```

  
You can find your API key [here](https://console.groq.com/keys).

## [Currently Unsupported OpenAI Features](#currently-unsupported-openai-features)

Note that although Groq API is mostly OpenAI compatible, there are a few features we don't support just yet:

### [Text Completions](#text-completions)

The following fields are currently not supported and will result in a 400 error (yikes) if they are supplied:

* `logprobs`
* `logit_bias`
* `top_logprobs`
* `messages[].name`
* If `N` is supplied, it must be equal to 1.

### [Temperature](#temperature)

If you set a `temperature` value of 0, it will be converted to `1e-8`. If you run into any issues, please try setting the value to a float32 `> 0` and `<= 2`.

### [Audio Transcription and Translation](#audio-transcription-and-translation)

The following values are not supported:

* `vtt`
* `srt`

## [Responses API](#responses-api)

Groq also supports the [Responses API](https://console.groq.com/docs/responses-api), which is a more advanced interface for generating model responses that supports both text and image inputs while producing text outputs. You can build stateful conversations by using previous responses as context, and extend your model's capabilities through function calling to connect with external systems and data sources.

### [Feedback](#feedback)

If you'd like to see support for such features as the above on Groq API, please reach out to us and let us know by submitting a "Feature Request" via "Chat with us" in the menu after clicking your organization in the top right. We really value your feedback and would love to hear from you! 🤩

## [Next Steps](#next-steps)

Migrate your prompts to open-source models using our [model migration guide](https://console.groq.com/docs/prompting/model-migration), or learn more about prompting in our [prompting guide](https://console.groq.com/docs/prompting).



---
description: Learn how to use the OpenAI-compatible Responses API with Groq, including built-in tools, tool use examples, and supported features.
title: Responses API - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Responses API

Groq's Responses API is fully compatible with OpenAI's Responses API, making it easy to integrate advanced conversational AI capabilities into your applications. The Responses API supports both text and image inputs while producing text outputs, stateful conversations, and function calling to connect with external systems.

The Responses API is currently in beta. Please let us know your feedback in our [Community](https://community.groq.com).

## [Configuring OpenAI Client for Responses API](#configuring-openai-client-for-responses-api)

To use the Responses API with OpenAI's client libraries, configure your client with your Groq API key and set the base URL to `https://api.groq.com/openai/v1`:

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-20b",
  input: "Tell me a fun fact about the moon in one sentence.",
});

console.log(response.output_text);
```

```
import openai

client = openai.OpenAI(
    api_key="your-groq-api-key",
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="llama-3.3-70b-versatile",
    input="Tell me a fun fact about the moon in one sentence.",
)

print(response.output_text)
```

```
curl https://api.groq.com/openai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "input": "Tell me a fun fact about the moon in one sentence."
  }'
```

You can find your API key [here](https://console.groq.com/keys).

## [Multi-turn Conversations](#multiturn-conversations)

The Responses API on Groq doesn't support stateful conversations yet, so you'll need to keep track of the conversation history yourself and provide it in every request.

Python

```
import OpenAI from "openai";
import * as readline from "readline";

const client = new OpenAI({
    apiKey: process.env.GROQ_API_KEY,
    baseURL: "https://api.groq.com/openai/v1",
});

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

function askQuestion(query) {
    return new Promise((resolve) => {
        rl.question(query, resolve);
    });
}

const messages = [];

async function main() {
    while (true) {
        const userInput = await askQuestion("You: ");

        if (userInput.toLowerCase().trim() === "stop") {
            console.log("Goodbye!");
            rl.close();
            break;
        }

        messages.push({
            role: "user",
            content: userInput,
        });

        const response = await client.responses.create({
            model: "openai/gpt-oss-20b",
            input: messages,
        });

        const assistantMessage = response.output_text;
        messages.push(...response.output);

        console.log(`Assistant: ${assistantMessage}`);
    }
}

main();
```

```
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

messages = []


def main():
    while True:
        user_input = input("You: ")

        if user_input.lower().strip() == "stop":
            print("Goodbye!")
            break

        messages.append({
            "role": "user",
            "content": user_input,
        })

        response = client.responses.create(
            model="openai/gpt-oss-20b",
            input=messages,
        )

        assistant_message = response.output_text
        messages.extend(response.output)

        print(f"Assistant: {assistant_message}")


if __name__ == "__main__":
    main()
```

## [Image Inputs](#image-inputs)

The Responses API supports image inputs with all [vision-capable models](https://console.groq.com/docs/vision). Here's an example of how to pass an image to the model:

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "meta-llama/llama-4-scout-17b-16e-instruct",
  input: [
    {
      role: "user",
      content: [
        {
            type: "input_text",
            text: "What are the main colors in this image? Give me the hex code for each color in a list."
        },
        {
            type: "input_image",
            detail: "auto",
            image_url: "https://console.groq.com/og_cloud.png"
        }
      ]
    }
  ],
});

console.log(response.output_text);
```

```
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

response = client.responses.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "What are the main colors in this image? Give me the hex code for each color in a list."
                },
                {
                    "type": "input_image",
                    "detail": "auto",
                    "image_url": "https://console.groq.com/og_cloud.png"
                }
            ]
        }
    ],
)

print(response.output_text)
```

```
curl -X POST https://api.groq.com/openai/v1/responses \
  -H "Authorization: Bearer ${GROQ_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "input": [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": "What are the main colors in this image? Give me the hex code for each color in a list."
          },
          {
            "type": "input_image",
            "detail": "auto",
            "image_url": "https://console.groq.com/og_cloud.png"
          }
        ]
      }
    ]
  }'
```

## [Built-In Tools](#builtin-tools)

In addition to a model's regular [tool use capabilities](https://console.groq.com/docs/tool-use), the Responses API supports various built-in tools to extend your model's capabilities.

### [Model Support](#model-support)

While all models support the Responses API, these built-in tools are only supported for the following models:

| Model ID                                               | Browser Search | Code Execution |
| ------------------------------------------------------ | -------------- | -------------- |
| [openai/gpt-oss-20b](https://console.groq.com/docs/model/openai/gpt-oss-20b)   | ✅              | ✅              |
| [openai/gpt-oss-120b](https://console.groq.com/docs/model/openai/gpt-oss-120b) | ✅              | ✅              |

Here are examples using code execution and browser search:

### [Code Execution Example](#code-execution-example)

Enable your models to write and execute Python code for calculations, data analysis, and problem-solving - see our [code execution documentation](https://console.groq.com/docs/code-execution) for more details.

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-20b",
  input: "What is 1312 X 3333? Output only the final answer.",
  tool_choice: "required",
  tools: [
    {
      type: "code_interpreter",
      container: {
        "type": "auto"
      }
    }
  ]
});

console.log(response.output_text);
```

```
import openai

client = openai.OpenAI(
    api_key="your-groq-api-key",
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-20b",
    input="What is 1312 X 3333? Output only the final answer.",
    tool_choice="required",
    tools=[
        {
            "type": "code_interpreter",
            "container": {
                "type": "auto"
            }
        }
    ]
)

print(response.output_text)
```

```
curl https://api.groq.com/openai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "input": "What is 1312 X 3333? Output only the final answer.",
    "tool_choice": "required",
    "tools": [
      {
        "type": "code_interpreter",
        "container": {
          "type": "auto"
        }
      }
    ]
  }'
```

### [Browser Search Example](#browser-search-example)

Give your models access to real-time web content and up-to-date information - see our [browser search documentation](https://console.groq.com/docs/browser-search) for more details.

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-20b",
  input: "Analyze the current weather in San Francisco and provide a detailed forecast.",
  tool_choice: "required",
  tools: [
    {
      type: "browser_search"
    }
  ]
});

console.log(response.output_text);
```

```
import openai

client = openai.OpenAI(
    api_key="your-groq-api-key",
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-20b",
    input="Analyze the current weather in San Francisco and provide a detailed forecast.",
    tool_choice="required",
    tools=[
        {
            "type": "browser_search"
        }
    ]
)

print(response.output_text)
```

```
curl https://api.groq.com/openai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "input": "Analyze the current weather in San Francisco and provide a detailed forecast.",
    "tool_choice": "required",
    "tools": [
      {
        "type": "browser_search"
      }
    ]
  }'
```

## [Structured Outputs](#structured-outputs)

Use structured outputs to ensure the model's response follows a specific JSON schema. This is useful for extracting structured data from text, ensuring consistent response formats, or integrating with downstream systems that expect specific data structures.

For a complete list of models that support structured outputs, see our [structured outputs documentation](https://console.groq.com/docs/structured-outputs).

Python

```
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await openai.responses.create({
  model: "openai/gpt-oss-120b",
  instructions: "Extract product review information from the text.",
  input: "I bought the UltraSound Headphones last week and I'm really impressed! The noise cancellation is amazing and the battery lasts all day. Sound quality is crisp and clear. I'd give it 4.5 out of 5 stars.",
  text: {
    format: {
      type: "json_schema",
      name: "product_review",
      schema: {
        type: "object",
        properties: {
          product_name: { type: "string" },
          rating: { type: "number" },
          sentiment: {
            type: "string",
            enum: ["positive", "negative", "neutral"]
          },
          key_features: {
            type: "array",
            items: { type: "string" }
          }
        },
        required: ["product_name", "rating", "sentiment", "key_features"],
        additionalProperties: false
      }
    }
  }
});

console.log(response.output_text);
```

```
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-120b",
    instructions="Extract product review information from the text.",
    input="I bought the UltraSound Headphones last week and I'm really impressed! The noise cancellation is amazing and the battery lasts all day. Sound quality is crisp and clear. I'd give it 4.5 out of 5 stars.",
    text={
        "format": {
            "type": "json_schema",
            "name": "product_review",
            "schema": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "rating": {"type": "number"},
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"]
                    },
                    "key_features": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["product_name", "rating", "sentiment", "key_features"],
                "additionalProperties": False
            }
        }
    }
)

print(response.output_text)
```

```
curl -X POST "https://api.groq.com/openai/v1/responses" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "instructions": "Extract product review information from the text.",
    "input": "I bought the UltraSound Headphones last week and I'\''m really impressed! The noise cancellation is amazing and the battery lasts all day. Sound quality is crisp and clear. I'\''d give it 4.5 out of 5 stars.",
    "text": {
      "format": {
        "type": "json_schema",
        "name": "product_review",
        "schema": {
          "type": "object",
          "properties": {
            "product_name": { "type": "string" },
            "rating": { "type": "number" },
            "sentiment": {
              "type": "string",
              "enum": ["positive", "negative", "neutral"]
            },
            "key_features": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["product_name", "rating", "sentiment", "key_features"],
          "additionalProperties": false
        }
      }
    }
  }'
```

Result

JSON

```
{
  "product_name": "UltraSound Headphones",
  "rating": 4.5,
  "sentiment": "positive",
  "key_features": [
      "noise cancellation",
      "long battery life",
      "crisp and clear sound quality"
  ]
}
```

### [Using a Schema Validation Library](#using-a-schema-validation-library)

When working with Structured Outputs, you can use popular schema validation libraries like [Zod](https://zod.dev/) for TypeScript and [Pydantic](https://docs.pydantic.dev/latest/) for Python. These libraries provide type safety, runtime validation, and seamless integration with JSON Schema generation.

Python

```
import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";

const openai = new OpenAI({
    apiKey: process.env.GROQ_API_KEY,
    baseURL: "https://api.groq.com/openai/v1",
});

const Recipe = z.object({
  title: z.string(),
  description: z.string(),
  prep_time_minutes: z.number(),
  cook_time_minutes: z.number(),
  ingredients: z.array(z.string()),
  instructions: z.array(z.string()),
});

const response = await openai.responses.parse({
  model: "openai/gpt-oss-20b",
  input: [
    { role: "system", content: "Create a recipe." },
    {
      role: "user",
      content: "Healthy chocolate coconut cake",
    },
  ],
  text: {
    format: zodTextFormat(Recipe, "recipe"),
  },
});

const recipe = response.output_parsed;
console.log(recipe);
```

```
import os
from openai import OpenAI
from pydantic import BaseModel


class Recipe(BaseModel):
    title: str
    description: str
    prep_time_minutes: int
    cook_time_minutes: int
    ingredients: list[str]
    instructions: list[str]


client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

response = client.responses.parse(
    model="openai/gpt-oss-20b",
    input=[
        {"role": "system", "content": "Create a recipe."},
        {
            "role": "user",
            "content": "Healthy chocolate coconut cake",
        },
    ],
    text_format=Recipe,
)

recipe = response.output_parsed
print(recipe)
```

## [Reasoning](#reasoning)

Use reasoning to let the model produce an internal chain of thought before generating a response. This is useful for complex problem solving, multi-step agentic workflow planning, and scientific analysis.

For a complete list of models that support reasoning, see our [reasoning documentation](https://console.groq.com/docs/reasoning).

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-20b",
  input: "How are AI models trained? Be brief.",
  reasoning: {
    effort: "low"
  }
});

console.log(response.output_text);
```

```
import openai

client = openai.OpenAI(
    api_key="your-groq-api-key",
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-20b",
    input="How are AI models trained? Be brief.",
    reasoning={
        "effort": "low"
    }
)

print(response.output_text)
```

```
curl https://api.groq.com/openai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "input": "How are AI models trained? Be brief.",
    "reasoning": {"effort": "low"}
  }'
```

Result

JSON

```
{
  "id": "resp_01k3hgcytaf7vawfkph3pef9qk",
  "object": "response",
  "status": "completed",
  "created_at": 1756155509,
  "output": [
    {
      "type": "reasoning",
      "id": "resp_01k3hgcytaf7vsyqqdk1932swk",
      "status": "completed",
      "content": [
        {
          "type": "reasoning_text",
          "text": "Need brief explanation."
        }
      ],
      "summary": []
    },
    {
      "type": "message",
      "id": "msg_01k3hgcytaf7w9wzkh0w18ww1q",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "AI models are trained by showing them many examples and adjusting their internal parameters so they make better predictions.1. **Define a task** (e.g., classify images, translate text, predict next word).  2. **Gather data**—a large set of input‑output pairs.  3. **Choose a model architecture** (e.g., neural network layers).  4. **Initialize weights** randomly or from a pre‑trained checkpoint.  5. **Feed data** through the network, compute an error (loss) between the model’s output and the true answer.  6. **Back‑propagate the error** to update the weights using an optimizer (e.g., SGD, Adam).  7. **Repeat** over many epochs until the loss stops improving.  8. **Validate** on a separate dataset to check generalization.  The process uses gradient descent and large‑scale computation (GPUs/TPUs) to handle the massive parameter count.",
          "annotations": [],
          "logprobs": null
        }
      ]
    }
  ],
  "previous_response_id": null,
  "model": "openai/gpt-oss-20b",
  "reasoning": {
    "effort": "low"
  },
  "max_output_tokens": null,
  "text": {
    "format": {
      "type": "text"
    }
  },
  "tools": [],
  "tool_choice": "auto",
  "truncation": "disabled",
  "metadata": {},
  "temperature": 1,
  "top_p": 1,
  "user": null,
  "service_tier": "default",
  "background": false,
  "error": null,
  "incomplete_details": null,
  "usage": {
    "input_tokens": 80,
    "input_tokens_details": {
      "cached_tokens": 0,
      "reasoning_tokens": 0
    },
    "output_tokens": 213,
    "output_tokens_details": {
      "cached_tokens": 0,
      "reasoning_tokens": 0
    },
    "total_tokens": 293
  },
  "parallel_tool_calls": true,
  "store": false,
  "top_logprobs": 0,
  "max_tool_calls": null
}
```

  
The reasoning traces can be found in the `result.output` array as type "reasoning":

Reasoning Traces

JSON

```
{
  "type": "reasoning",
  "id": "resp_01k3hgcytaf7vsyqqdk1932swk",
  "status": "completed",
  "content": [
    {
      "type": "reasoning_text",
      "text": "Need brief explanation."
    }
  ],
  "summary": []
},
```

## [Model Context Protocol (MCP)](#model-context-protocol-mcp)

The Responses API also supports the [Model Context Protocol (MCP)](https://console.groq.com/docs/mcp), an open-source standard that enables AI applications to connect with external systems like databases, APIs, and tools. MCP provides a standardized way for AI models to access and interact with your data and workflows.

With MCP, you can build AI agents that access your codebase through GitHub, query databases with natural language, browse the web for real-time information, or connect to any API-based service like Slack, Notion, or Google Calendar.

### [MCP Example](#mcp-example)

Here's an example using [Hugging Face's MCP server](https://huggingface.co/settings/mcp) to search for trending AI models.

Python

```
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

const response = await client.responses.create({
  model: "openai/gpt-oss-120b",
  input: "What models are trending on Huggingface?",
  tools: [
    {
      type: "mcp",
      server_label: "Huggingface",
      server_url: "https://huggingface.co/mcp",
    }
  ]
});

console.log(response);
```

```
import openai
import os

client = openai.OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-120b",
    input="What models are trending on Huggingface?",
    tools=[
        {
            "type": "mcp",
            "server_label": "Huggingface",
            "server_url": "https://huggingface.co/mcp",
        }
    ]
)

print(response)
```

```
curl -X POST "https://api.groq.com/openai/v1/responses" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": "What models are trending on Huggingface?",
    "tools": [
      {
        "type": "mcp",
        "server_label": "Huggingface",
        "server_url": "https://huggingface.co/mcp"
      }
    ]
  }'
```

For comprehensive examples including GitHub integration, web search, and payment processing, see our full [MCP documentation](https://console.groq.com/docs/mcp).

## [Unsupported Features](#unsupported-features)

Although Groq's Responses API is mostly compatible with OpenAI's Responses API, there are a few features we don't support just yet:

* `previous_response_id`
* `store`
* `truncation`
* `include`
* `safety_identifier`
* `prompt_cache_key`
* `prompt` (reusable prompts)

Want to see one of these features supported? Let us know on our [Community forum](https://community.groq.com)!

## [Detailed Usage Metrics](#detailed-usage-metrics)

To include detailed usage metrics for each request (such as exact inference time), set the following header:

curl

```
Groq-Beta: inference-metrics
```

In the response body, the `metadata` field will include the following keys:

* `completion_time`: The time in seconds it took to generate the output
* `prompt_time`: The time in seconds it took to process the input prompt
* `queue_time`: The time in seconds the requests was queued before being processed
* `total_time`: The total time in seconds it took to process the request

JSON

```
{
  "metadata": {
    "completion_time": "2.567331286",
    "prompt_time": "0.003652567",
    "queue_time": "0.018393202",
    "total_time": "2.570983853"
  }
}
```

To calculate output tokens per second, combine the information from the `usage` field with the `metadata` field:

curl

```
output_tokens_per_second = usage.output_tokens / metadata.completion_time
```

## [Next Steps](#next-steps)

Explore more advanced use cases in our built-in [browser search](https://console.groq.com/docs/browser-search) and [code execution](https://console.groq.com/docs/code-execution) documentation, or learn about connecting to external systems with [MCP](https://console.groq.com/docs/mcp).



---
description: Understand Groq API rate limits, headers, and best practices for managing request and token quotas in your applications.
title: Rate Limits - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Rate Limits

Rate limits act as control measures to regulate how frequently users and applications can access our API within specified timeframes. These limits help ensure service stability, fair access, and protection against misuse so that we can serve reliable and fast inference for all.

## [Understanding Rate Limits](#understanding-rate-limits)

Rate limits are measured in:

* **RPM:** Requests per minute
* **RPD:** Requests per day
* **TPM:** Tokens per minute
* **TPD:** Tokens per day
* **ASH:** Audio seconds per hour
* **ASD:** Audio seconds per day

[Cached tokens](https://console.groq.com/docs/prompt-caching) do not count towards your rate limits.

Rate limits apply at the organization level, not individual users. You can hit any limit type depending on which threshold you reach first.

**Example:** Let's say your RPM = 50 and your TPM = 200K. If you were to send 50 requests with only 100 tokens within a minute, you would reach your limit even though you did not send 200K tokens within those 50 requests.

## [Rate Limits](#rate-limits)

The following is a high level summary and there may be exceptions to these limits. You can view the current, exact rate limits for your organization on the [limits page](https://console.groq.com/settings/limits) in your account settings.

**Need higher rate limits?** Upgrade to [Developer plan](https://console.groq.com/settings/billing/plans) to access higher limits, [Batch](https://console.groq.com/docs/batch) and [Flex](https://console.groq.com/docs/flex-processing) processing, and more. Note that the limits shown below are the base limits for the Developer plan, and higher limits are available for select workloads and enterprise use cases.

| MODEL ID | RPM | RPD | TPM | TPD | ASH | ASD |
| -------- | --- | --- | --- | --- | --- | --- |

| allam-2-7b                                | 30 | 7K    | 6K   | 500K | \-   | \-    |
| ----------------------------------------- | -- | ----- | ---- | ---- | ---- | ----- |
| canopylabs/orpheus-arabic-saudi           | 10 | 100   | 1.2K | 3.6K | \-   | \-    |
| canopylabs/orpheus-v1-english             | 10 | 100   | 1.2K | 3.6K | \-   | \-    |
| groq/compound                             | 30 | 250   | 70K  | \-   | \-   | \-    |
| groq/compound-mini                        | 30 | 250   | 70K  | \-   | \-   | \-    |
| llama-3.1-8b-instant                      | 30 | 14.4K | 6K   | 500K | \-   | \-    |
| llama-3.3-70b-versatile                   | 30 | 1K    | 12K  | 100K | \-   | \-    |
| meta-llama/llama-4-scout-17b-16e-instruct | 30 | 1K    | 30K  | 500K | \-   | \-    |
| meta-llama/llama-prompt-guard-2-22m       | 30 | 14.4K | 15K  | 500K | \-   | \-    |
| meta-llama/llama-prompt-guard-2-86m       | 30 | 14.4K | 15K  | 500K | \-   | \-    |
| moonshotai/kimi-k2-instruct               | 60 | 1K    | 10K  | 300K | \-   | \-    |
| moonshotai/kimi-k2-instruct-0905          | 60 | 1K    | 10K  | 300K | \-   | \-    |
| openai/gpt-oss-120b                       | 30 | 1K    | 8K   | 200K | \-   | \-    |
| openai/gpt-oss-20b                        | 30 | 1K    | 8K   | 200K | \-   | \-    |
| openai/gpt-oss-safeguard-20b              | 30 | 1K    | 8K   | 200K | \-   | \-    |
| qwen/qwen3-32b                            | 60 | 1K    | 6K   | 500K | \-   | \-    |
| whisper-large-v3                          | 20 | 2K    | \-   | \-   | 7.2K | 28.8K |
| whisper-large-v3-turbo                    | 20 | 2K    | \-   | \-   | 7.2K | 28.8K |

## [Rate Limit Headers](#rate-limit-headers)

In addition to viewing your limits on your account's [limits](https://console.groq.com/settings/limits) page, you can also view rate limit information such as remaining requests and tokens in HTTP response headers as follows:

The following headers are set (values are illustrative):

| Header                         | Value    | Notes                                    |
| ------------------------------ | -------- | ---------------------------------------- |
| retry-after                    | 2        | In seconds                               |
| x-ratelimit-limit-requests     | 14400    | Always refers to Requests Per Day (RPD)  |
| x-ratelimit-limit-tokens       | 18000    | Always refers to Tokens Per Minute (TPM) |
| x-ratelimit-remaining-requests | 14370    | Always refers to Requests Per Day (RPD)  |
| x-ratelimit-remaining-tokens   | 17997    | Always refers to Tokens Per Minute (TPM) |
| x-ratelimit-reset-requests     | 2m59.56s | Always refers to Requests Per Day (RPD)  |
| x-ratelimit-reset-tokens       | 7.66s    | Always refers to Tokens Per Minute (TPM) |

## [Handling Rate Limits](#handling-rate-limits)

When you exceed rate limits, our API returns a `429 Too Many Requests` HTTP status code.

**Note**: `retry-after` is only set if you hit the rate limit and status code 429 is returned. The other headers are always included.



---
description: Learn how to generate text and have conversations with Groq&#x27;s Chat Completions API, including streaming, JSON mode, and advanced features.
title: Text Generation - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Text Generation

Generating text with Groq's Chat Completions API enables you to have natural, conversational interactions with Groq's large language models. It processes a series of messages and generates human-like responses that can be used for various applications including conversational agents, content generation, task automation, and generating structured data outputs like JSON for your applications.

## [Chat Completions](#chat-completions)

Chat completions allow your applications to have dynamic interactions with Groq's models. You can send messages that include user inputs and system instructions, and receive responses that match the conversational context.

  
Chat models can handle both multi-turn discussions (conversations with multiple back-and-forth exchanges) and single-turn tasks where you need just one response.

  
For details about all available parameters, [visit the API reference page.](https://console.groq.com/docs/api-reference#chat-create)

### [Getting Started with Groq SDK](#getting-started-with-groq-sdk)

To start using Groq's Chat Completions API, you'll need to install the [Groq SDK](https://console.groq.com/docs/libraries) and set up your [API key](https://console.groq.com/keys).

PythonJavaScript

shell

```
pip install groq
```

## [Performing a Basic Chat Completion](#performing-a-basic-chat-completion)

The simplest way to use the Chat Completions API is to send a list of messages and receive a single response. Messages are provided in chronological order, with each message containing a role ("system", "user", or "assistant") and content.

Python

```
from groq import Groq

client = Groq()

chat_completion = client.chat.completions.create(
    messages=[
        # Set an optional system message. This sets the behavior of the
        # assistant and can be used to provide specific instructions for
        # how it should behave throughout the conversation.
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        # Set a user message for the assistant to respond to.
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],

    # The language model which will generate the completion.
    model="llama-3.3-70b-versatile"
)

# Print the completion returned by the LLM.
print(chat_completion.choices[0].message.content)
```

## [Streaming a Chat Completion](#streaming-a-chat-completion)

For a more responsive user experience, you can stream the model's response in real-time. This allows your application to display the response as it's being generated, rather than waiting for the complete response.

To enable streaming, set the parameter `stream=True`. The completion function will then return an iterator of completion deltas rather than a single, full completion.

Python

```
from groq import Groq

client = Groq()

stream = client.chat.completions.create(
    #
    # Required parameters
    #
    messages=[
        # Set an optional system message. This sets the behavior of the
        # assistant and can be used to provide specific instructions for
        # how it should behave throughout the conversation.
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        # Set a user message for the assistant to respond to.
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],

    # The language model which will generate the completion.
    model="llama-3.3-70b-versatile",

    #
    # Optional parameters
    #

    # Controls randomness: lowering results in less random completions.
    # As the temperature approaches zero, the model will become deterministic
    # and repetitive.
    temperature=0.5,

    # The maximum number of tokens to generate. Requests can use up to
    # 2048 tokens shared between prompt and completion.
    max_completion_tokens=1024,

    # Controls diversity via nucleus sampling: 0.5 means half of all
    # likelihood-weighted options are considered.
    top_p=1,

    # A stop sequence is a predefined or user-specified text string that
    # signals an AI to stop generating content, ensuring its responses
    # remain focused and concise. Examples include punctuation marks and
    # markers like "[end]".
    stop=None,

    # If set, partial message deltas will be sent.
    stream=True,
)

# Print the incremental deltas returned by the LLM.
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

## [Performing a Chat Completion with a Stop Sequence](#performing-a-chat-completion-with-a-stop-sequence)

Stop sequences allow you to control where the model should stop generating. When the model encounters any of the specified stop sequences, it will halt generation at that point. This is useful when you need responses to end at specific points.

Python

```
from groq import Groq

client = Groq()

chat_completion = client.chat.completions.create(
    #
    # Required parameters
    #
    messages=[
        # Set an optional system message. This sets the behavior of the
        # assistant and can be used to provide specific instructions for
        # how it should behave throughout the conversation.
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        # Set a user message for the assistant to respond to.
        {
            "role": "user",
            "content": "Count to 10.  Your response must begin with \"1, \".  example: 1, 2, 3, ...",
        }
    ],

    # The language model which will generate the completion.
    model="llama-3.3-70b-versatile",

    #
    # Optional parameters
    #

    # Controls randomness: lowering results in less random completions.
    # As the temperature approaches zero, the model will become deterministic
    # and repetitive.
    temperature=0.5,

    # The maximum number of tokens to generate. Requests can use up to
    # 2048 tokens shared between prompt and completion.
    max_completion_tokens=1024,

    # Controls diversity via nucleus sampling: 0.5 means half of all
    # likelihood-weighted options are considered.
    top_p=1,

    # A stop sequence is a predefined or user-specified text string that
    # signals an AI to stop generating content, ensuring its responses
    # remain focused and concise. Examples include punctuation marks and
    # markers like "[end]".
    # For this example, we will use ", 6" so that the llm stops counting at 5.
    # If multiple stop values are needed, an array of string may be passed,
    # stop=[", 6", ", six", ", Six"]
    stop=", 6",

    # If set, partial message deltas will be sent.
    stream=False,
)

# Print the completion returned by the LLM.
print(chat_completion.choices[0].message.content)
```

## [Performing an Async Chat Completion](#performing-an-async-chat-completion)

For applications that need to maintain responsiveness while waiting for completions, you can use the asynchronous client. This lets you make non-blocking API calls using Python's asyncio framework.

Python

```
import asyncio

from groq import AsyncGroq


async def main():
    client = AsyncGroq()

    chat_completion = await client.chat.completions.create(
        #
        # Required parameters
        #
        messages=[
            # Set an optional system message. This sets the behavior of the
            # assistant and can be used to provide specific instructions for
            # how it should behave throughout the conversation.
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            # Set a user message for the assistant to respond to.
            {
                "role": "user",
                "content": "Explain the importance of fast language models",
            }
        ],

        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",

        #
        # Optional parameters
        #

        # Controls randomness: lowering results in less random completions.
        # As the temperature approaches zero, the model will become
        # deterministic and repetitive.
        temperature=0.5,

        # The maximum number of tokens to generate. Requests can use up to
        # 2048 tokens shared between prompt and completion.
        max_completion_tokens=1024,

        # Controls diversity via nucleus sampling: 0.5 means half of all
        # likelihood-weighted options are considered.
        top_p=1,

        # A stop sequence is a predefined or user-specified text string that
        # signals an AI to stop generating content, ensuring its responses
        # remain focused and concise. Examples include punctuation marks and
        # markers like "[end]".
        stop=None,

        # If set, partial message deltas will be sent.
        stream=False,
    )

    # Print the completion returned by the LLM.
    print(chat_completion.choices[0].message.content)

asyncio.run(main())
```

### [Streaming an Async Chat Completion](#streaming-an-async-chat-completion)

You can combine the benefits of streaming and asynchronous processing by streaming completions asynchronously. This is particularly useful for applications that need to handle multiple concurrent conversations.

Python

```
import asyncio

from groq import AsyncGroq


async def main():
    client = AsyncGroq()

    stream = await client.chat.completions.create(
        #
        # Required parameters
        #
        messages=[
            # Set an optional system message. This sets the behavior of the
            # assistant and can be used to provide specific instructions for
            # how it should behave throughout the conversation.
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            # Set a user message for the assistant to respond to.
            {
                "role": "user",
                "content": "Explain the importance of fast language models",
            }
        ],

        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",

        #
        # Optional parameters
        #

        # Controls randomness: lowering results in less random completions.
        # As the temperature approaches zero, the model will become
        # deterministic and repetitive.
        temperature=0.5,

        # The maximum number of tokens to generate. Requests can use up to
        # 2048 tokens shared between prompt and completion.
        max_completion_tokens=1024,

        # Controls diversity via nucleus sampling: 0.5 means half of all
        # likelihood-weighted options are considered.
        top_p=1,

        # A stop sequence is a predefined or user-specified text string that
        # signals an AI to stop generating content, ensuring its responses
        # remain focused and concise. Examples include punctuation marks and
        # markers like "[end]".
        stop=None,

        # If set, partial message deltas will be sent.
        stream=True,
    )

    # Print the incremental deltas returned by the LLM.
    async for chunk in stream:
        print(chunk.choices[0].delta.content, end="")

asyncio.run(main())
```

## [Structured Outputs and JSON](#structured-outputs-and-json)

Need reliable, type-safe JSON responses that match your exact schema? Groq's Structured Outputs feature is designed so that model responses strictly conform to your JSON Schema without validation or retry logic.

  
For complete guides on implementing structured outputs with JSON Schema or using JSON Object Mode, see our [structured outputs documentation](https://console.groq.com/docs/structured-outputs).

  
Key capabilities:

* **JSON Schema enforcement**: Responses match your schema exactly
* **Type-safe outputs**: No validation or retry logic needed
* **Programmatic refusal detection**: Handle safety-based refusals programmatically
* **JSON Object Mode**: Basic JSON output with prompt-guided structure




---
description: Integrate Groq&#x27;s fast speech-to-text API for instant audio transcription and translation in your applications.
title: Speech to Text - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Speech to Text

Groq API is designed to provide fast speech-to-text solution available, offering OpenAI-compatible endpoints that enable near-instant transcriptions and translations. With Groq API, you can integrate high-quality audio processing into your applications at speeds that rival human interaction.

## [API Endpoints](#api-endpoints)

We support two endpoints:

| Endpoint       | Usage                           | API Endpoint                                        |
| -------------- | ------------------------------- | --------------------------------------------------- |
| Transcriptions | Convert audio to text           | https://api.groq.com/openai/v1/audio/transcriptions |
| Translations   | Translate audio to English text | https://api.groq.com/openai/v1/audio/translations   |

## [Supported Models](#supported-models)

| Model ID               | Model                                                        | Supported Language(s) | Description                                                                                                    |
| ---------------------- | ------------------------------------------------------------ | --------------------- | -------------------------------------------------------------------------------------------------------------- |
| whisper-large-v3-turbo | [Whisper Large V3 Turbo](https://console.groq.com/docs/model/whisper-large-v3-turbo) | Multilingual          | A fine-tuned version of a pruned Whisper Large V3 designed for fast, multilingual transcription tasks.         |
| whisper-large-v3       | [Whisper Large V3](https://console.groq.com/docs/model/whisper-large-v3)             | Multilingual          | Provides state-of-the-art performance with high accuracy for multilingual transcription and translation tasks. |

## [Which Whisper Model Should You Use?](#which-whisper-model-should-you-use)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the tradeoffs between models to find the one most suitable for your applications:

* If your application is error-sensitive and requires multilingual support, use  
`whisper-large-v3`  
.
* If your application requires multilingual support and you need the best price for performance, use  
`whisper-large-v3-turbo`  
.

The following table breaks down the metrics for each model.

| Model                  | Cost Per Hour | Language Support | Transcription Support | Translation Support | Real-time Speed Factor | Word Error Rate |
| ---------------------- | ------------- | ---------------- | --------------------- | ------------------- | ---------------------- | --------------- |
| whisper-large-v3       | $0.111        | Multilingual     | Yes                   | Yes                 | 189                    | 10.3%           |
| whisper-large-v3-turbo | $0.04         | Multilingual     | Yes                   | No                  | 216                    | 12%             |

## [Working with Audio Files](#working-with-audio-files)

### Audio File Limitations

Max File Size

25 MB (free tier), 100MB (dev tier)

Max Attachment File Size

25 MB. If you need to process larger files, use the `url` parameter to specify a url to the file instead.

Minimum File Length

0.01 seconds

Minimum Billed Length

10 seconds. If you submit a request less than this, you will still be billed for 10 seconds.

Supported File Types

Either a URL or a direct file upload for `flac`, `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `ogg`, `wav`, `webm`

Single Audio Track

Only the first track will be transcribed for files with multiple audio tracks. (e.g. dubbed video)

Supported Response Formats

`json`, `verbose_json`, `text`

Supported Timestamp Granularities

`segment`, `word`

### [Audio Preprocessing](#audio-preprocessing)

Our speech-to-text models will downsample audio to 16KHz mono before transcribing, which is optimal for speech recognition. This preprocessing can be performed client-side if your original file is extremely large and you want to make it smaller without a loss in quality (without chunking, Groq API speech-to-text endpoints accept up to 25MB for free tier and 100MB for [dev tier](https://console.groq.com/settings/billing)). For lower latency, convert your files to `wav` format. When reducing file size, we recommend FLAC for lossless compression.

The following `ffmpeg` command can be used to reduce file size:

shell

```
ffmpeg \
  -i <your file> \
  -ar 16000 \
  -ac 1 \
  -map 0:a \
  -c:a flac \
  <output file name>.flac
```

### [Working with Larger Audio Files](#working-with-larger-audio-files)

For audio files that exceed our size limits or require more precise control over transcription, we recommend implementing audio chunking. This process involves:

1. Breaking the audio into smaller, overlapping segments
2. Processing each segment independently
3. Combining the results while handling overlapping

[To learn more about this process and get code for your own implementation, see the complete audio chunking tutorial in our Groq API Cookbook. ](https://github.com/groq/groq-api-cookbook/tree/main/tutorials/audio-chunking)

## [Using the API](#using-the-api)

The following are request parameters you can use in your transcription and translation requests:

| Parameter                    | Type   | Default                            | Description                                                                                                                                                                                                                                                                                                                                                                     |
| ---------------------------- | ------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| file                         | string | Required unless using url instead  | The audio file object for direct upload to translate/transcribe.                                                                                                                                                                                                                                                                                                                |
| url                          | string | Required unless using file instead | The audio URL to translate/transcribe (supports Base64URL).                                                                                                                                                                                                                                                                                                                     |
| language                     | string | Optional                           | The language of the input audio. Supplying the input language in ISO-639-1 (i.e. en, tr\`) format will improve accuracy and latency.The translations endpoint only supports 'en' as a parameter option.                                                                                                                                                                         |
| model                        | string | Required                           | ID of the model to use.                                                                                                                                                                                                                                                                                                                                                         |
| prompt                       | string | Optional                           | Prompt to guide the model's style or specify how to spell unfamiliar words. (limited to 224 tokens)                                                                                                                                                                                                                                                                             |
| response\_format             | string | json                               | Define the output response format.Set to verbose\_json to receive timestamps for audio segments.Set to text to return a text response.                                                                                                                                                                                                                                          |
| temperature                  | float  | 0                                  | The temperature between 0 and 1\. For translations and transcriptions, we recommend the default value of 0.                                                                                                                                                                                                                                                                     |
| timestamp\_granularities\[\] | array  | segment                            | The timestamp granularities to populate for this transcription. response\_format must be set verbose\_json to use timestamp granularities.Either or both of word and segment are supported. segment returns full metadata and word returns only word, start, and end timestamps. To get both word-level timestamps and full segment metadata, include both values in the array. |

### [Example Usage of Transcription Endpoint](#example-usage-of-transcription-endpoint)

The transcription endpoint allows you to transcribe spoken words in audio or video files.

PythonJavaScriptcurl

The Groq SDK package can be installed using the following command:

shell

```
pip install groq
```

The following code snippet demonstrates how to use Groq API to transcribe an audio file in Python:

Python

```
import os
import json
from groq import Groq

# Initialize the Groq client
client = Groq()

# Specify the path to the audio file
filename = os.path.dirname(__file__) + "/YOUR_AUDIO.wav" # Replace with your audio file!

# Open the audio file
with open(filename, "rb") as file:
    # Create a transcription of the audio file
    transcription = client.audio.transcriptions.create(
      file=file, # Required audio file
      model="whisper-large-v3-turbo", # Required model to use for transcription
      prompt="Specify context or spelling",  # Optional
      response_format="verbose_json",  # Optional
      timestamp_granularities = ["word", "segment"], # Optional (must set response_format to "json" to use and can specify "word", "segment" (default), or both)
      language="en",  # Optional
      temperature=0.0  # Optional
    )
    # To print only the transcription text, you'd use print(transcription.text) (here we're printing the entire transcription object to access timestamps)
    print(json.dumps(transcription, indent=2, default=str))
```

### [Example Usage of Translation Endpoint](#example-usage-of-translation-endpoint)

The translation endpoint allows you to translate spoken words in audio or video files to English.

PythonJavaScriptcurl

The Groq SDK package can be installed using the following command:

shell

```
pip install groq
```

The following code snippet demonstrates how to use Groq API to translate an audio file in Python:

Python

```
import os
from groq import Groq

# Initialize the Groq client
client = Groq()

# Specify the path to the audio file
filename = os.path.dirname(__file__) + "/sample_audio.m4a" # Replace with your audio file!

# Open the audio file
with open(filename, "rb") as file:
    # Create a translation of the audio file
    translation = client.audio.translations.create(
      file=(filename, file.read()), # Required audio file
      model="whisper-large-v3", # Required model to use for translation
      prompt="Specify context or spelling",  # Optional
      language="en", # Optional ('en' only)
      response_format="json",  # Optional
      temperature=0.0  # Optional
    )
    # Print the translation text
    print(translation.text)
```

## [Understanding Metadata Fields](#understanding-metadata-fields)

When working with Groq API, setting `response_format` to `verbose_json` outputs each segment of transcribed text with valuable metadata that helps us understand the quality and characteristics of our transcription, including `avg_logprob`, `compression_ratio`, and `no_speech_prob`.

This information can help us with debugging any transcription issues. Let's examine what this metadata tells us using a real example:

JSON

```
{
  "id": 8,
  "seek": 3000,
  "start": 43.92,
  "end": 50.16,
  "text": " document that the functional specification that you started to read through that isn't just the",
  "tokens": [51061, 4166, 300, 264, 11745, 31256],
  "temperature": 0,
  "avg_logprob": -0.097569615,
  "compression_ratio": 1.6637554,
  "no_speech_prob": 0.012814695
}
```

As shown in the above example, we receive timing information as well as quality indicators. Let's gain a better understanding of what each field means:

* `id:8`: The 9th segment in the transcription (counting begins at 0)
* `seek`: Indicates where in the audio file this segment begins (3000 in this case)
* `start` and `end` timestamps: Tell us exactly when this segment occurs in the audio (43.92 to 50.16 seconds in our example)
* `avg_logprob` (Average Log Probability): -0.097569615 in our example indicates very high confidence. Values closer to 0 suggest better confidence, while more negative values (like -0.5 or lower) might indicate transcription issues.
* `no_speech_prob` (No Speech Probability): 0.0.012814695 is very low, suggesting this is definitely speech. Higher values (closer to 1) would indicate potential silence or non-speech audio.
* `compression_ratio`: 1.6637554 is a healthy value, indicating normal speech patterns. Unusual values (very high or low) might suggest issues with speech clarity or word boundaries.

### [Using Metadata for Debugging](#using-metadata-for-debugging)

When troubleshooting transcription issues, look for these patterns:

* Low Confidence Sections: If `avg_logprob` drops significantly (becomes more negative), check for background noise, multiple speakers talking simultaneously, unclear pronunciation, and strong accents. Consider cleaning up the audio in these sections or adjusting chunk sizes around problematic chunk boundaries.
* Non-Speech Detection: High `no_speech_prob` values might indicate silence periods that could be trimmed, background music or noise, or non-verbal sounds being misinterpreted as speech. Consider noise reduction when preprocessing.
* Unusual Speech Patterns: Unexpected `compression_ratio` values can reveal stuttering or word repetition, speaker talking unusually fast or slow, or audio quality issues affecting word separation.

### [Quality Thresholds and Regular Monitoring](#quality-thresholds-and-regular-monitoring)

We recommend setting acceptable ranges for each metadata value we reviewed above and flagging segments that fall outside these ranges to be able to identify and adjust preprocessing or chunking strategies for flagged sections.

By understanding and monitoring these metadata values, you can significantly improve your transcription quality and quickly identify potential issues in your audio processing pipeline.

### [Prompting Guidelines](#prompting-guidelines)

The prompt parameter (max 224 tokens) helps provide context and maintain a consistent output style. Unlike chat completion prompts, these prompts only guide style and context, not specific actions.

Best Practices

* Provide relevant context about the audio content, such as the type of conversation, topic, or speakers involved.
* Use the same language as the language of the audio file.
* Steer the model's output by denoting proper spellings or emulate a specific writing style or tone.
* Keep the prompt concise and focused on stylistic guidance.



---
description: Instantly generate lifelike audio from text using Groq&#x27;s fast text-to-speech API with support for multiple voices and languages.
title: Text to Speech - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Text to Speech

Learn how to instantly generate lifelike audio from text.

## [Overview](#overview)

The Groq API speech endpoint provides fast text-to-speech (TTS), enabling you to convert text to spoken audio in seconds. With support for English and Arabic voices, you can create life-like audio content for customer support agents, game characters, narration, and more.

## [API Endpoint](#api-endpoint)

| Endpoint | Usage                 | API Endpoint                                |
| -------- | --------------------- | ------------------------------------------- |
| Speech   | Convert text to audio | https://api.groq.com/openai/v1/audio/speech |

## [Supported Models](#supported-models)

| Model ID                                                                       | Language       | Description                                  |
| ------------------------------------------------------------------------------ | -------------- | -------------------------------------------- |
| [canopylabs/orpheus-v1-english](https://console.groq.com/docs/model/canopylabs/orpheus-v1-english)     | English        | Expressive TTS with vocal direction controls |
| [canopylabs/orpheus-arabic-saudi](https://console.groq.com/docs/model/canopylabs/orpheus-arabic-saudi) | Arabic (Saudi) | Authentic Saudi dialect synthesis            |

## [Quick Start](#quick-start)

The speech endpoint takes four key inputs:

* **model:** `canopylabs/orpheus-v1-english` or `canopylabs/orpheus-arabic-saudi`
* **input:** the text to generate audio from
* **voice:** the desired voice for output
* **response format:** defaults to `"wav"`

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "orpheus-english.wav" 
model = "canopylabs/orpheus-v1-english"
voice = "troy"
text = "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support."
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)
```

```
import fs from "fs";
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY
});

const speechFilePath = "orpheus-english.wav";
const model = "canopylabs/orpheus-v1-english";
const voice = "hannah";
const text = "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support.";
const responseFormat = "wav";

async function main() {
  const response = await groq.audio.speech.create({
    model: model,
    voice: voice,
    input: text,
    response_format: responseFormat
  });
  
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.promises.writeFile(speechFilePath, buffer);
  
  console.log(`Orpheus English speech generated: ${speechFilePath}`);
}

main().catch((error) => {
  console.error('Error generating speech:', error);
});
```

```
curl https://api.groq.com/openai/v1/audio/speech \
  -X POST \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "canopylabs/orpheus-v1-english",
    "input": "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support.",
    "voice": "austin",
    "response_format": "wav"
  }' \
  --output orpheus-english.wav
```

## [Next Steps](#next-steps)

For comprehensive documentation on available voices, vocal directions, use cases, and best practices, see the Orpheus documentation:

[Orpheus Text to SpeechLearn about vocal directions, available voices, use cases, and best practices for generating expressive speech](https://console.groq.com/docs/text-to-speech/orpheus)


---
description: Generate expressive speech audio from text using Orpheus v1 models with vocal directions support - available in English and Arabic Saudi dialect.
title: Orpheus Text to Speech - GroqDocs
image: https://console.groq.com/og_cloudv5.jpg
---

# Orpheus Text to Speech

Generate expressive, natural-sounding speech with vocal direction controls for dynamic audio output.

## [Overview](#overview)

Orpheus text-to-speech models by [Canopy Labs](https://canopylabs.ai/) provide fast, high-quality audio generation with unique expressive capabilities. Both models offer multiple voices and low-latency inference, with the English model supporting [vocal direction controls](#vocal-directions) for expressive performances.

## [Supported Models](#supported-models)

Groq hosts two specialized Orpheus models for different language needs:

| Model ID                                                                       | Description                                   | Language       | Vocal Directions |
| ------------------------------------------------------------------------------ | --------------------------------------------- | -------------- | ---------------- |
| [canopylabs/orpheus-v1-english](https://console.groq.com/docs/model/canopylabs/orpheus-v1-english)     | Expressive English TTS with direction support | English        | ✅ Supported      |
| [canopylabs/orpheus-arabic-saudi](https://console.groq.com/docs/model/canopylabs/orpheus-arabic-saudi) | Authentic Saudi dialect synthesis             | Arabic (Saudi) | ❌ Not Supported  |

## [Pricing](#pricing)

| Model ID                        | Price                      |
| ------------------------------- | -------------------------- |
| canopylabs/orpheus-v1-english   | $22 / 1 million characters |
| canopylabs/orpheus-arabic-saudi | $40 / 1 million characters |

## [API Endpoint](#api-endpoint)

| Endpoint | Usage                 | API Endpoint                                |
| -------- | --------------------- | ------------------------------------------- |
| Speech   | Convert text to audio | https://api.groq.com/openai/v1/audio/speech |

## [Quick Start](#quick-start)

The speech endpoint accepts these parameters:

| Parameter        | Type   | Required | Description                                                                                                |
| ---------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------------- |
| model            | string | Yes      | Model ID: canopylabs/orpheus-v1-english or canopylabs/orpheus-arabic-saudi                                 |
| input            | string | Yes      | Text to convert to speech (max 200 characters). Use \[directions\] for [vocal control](#vocal-directions). |
| voice            | string | Yes      | Voice persona ID to use (see [Available Voices](#available-voices))                                        |
| response\_format | string | Optional | Audio format. Defaults to "wav". The only supported format is "wav".                                       |

## [Basic Usage](#basic-usage)

EnglishArabic Saudi Dialect

### [English Model](#english-model)

Python

```
# Install the Groq SDK:
# pip install groq

# English Model Example:
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "orpheus-english.wav" 
model = "canopylabs/orpheus-v1-english"
voice = "troy"
text = "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support."
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)
```

```
// Install the Groq SDK:
// npm install --save groq-sdk

// English Model Example:
import fs from "fs";
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY
});

const speechFilePath = "orpheus-english.wav";
const model = "canopylabs/orpheus-v1-english";
const voice = "hannah";
const text = "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support.";
const responseFormat = "wav";

async function main() {
  const response = await groq.audio.speech.create({
    model: model,
    voice: voice,
    input: text,
    response_format: responseFormat
  });
  
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.promises.writeFile(speechFilePath, buffer);
  
  console.log(`Orpheus English speech generated: ${speechFilePath}`);
}

main().catch((error) => {
  console.error('Error generating speech:', error);
});
```

```
curl https://api.groq.com/openai/v1/audio/speech \
  -X POST \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "canopylabs/orpheus-v1-english",
    "input": "Welcome to Orpheus text-to-speech. [cheerful] This is an example of high-quality English audio generation with vocal directions support.",
    "voice": "austin",
    "response_format": "wav"
  }' \
  --output orpheus-english.wav
```

### [Arabic Saudi Dialect Model](#arabic-saudi-dialect-model)

Python

```
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "orpheus-arabic.wav" 
model = "canopylabs/orpheus-arabic-saudi"
voice = "fahad"
text = "مرحبا بكم في نموذج أورفيوس للتحويل من النص إلى الكلام. هذا مثال على جودة الصوت العربية السعودية الطبيعية."
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)
```

```
import fs from "fs";
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY
});

const speechFilePath = "orpheus-arabic.wav";
const model = "canopylabs/orpheus-arabic-saudi";
const voice = "lulwa";
const text = "مرحبا بكم في نموذج أورفيوس للتحويل من النص إلى الكلام. هذا مثال على جودة الصوت العربية السعودية الطبيعية.";
const responseFormat = "wav";

async function main() {
  const response = await groq.audio.speech.create({
    model: model,
    voice: voice,
    input: text,
    response_format: responseFormat
  });
  
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.promises.writeFile(speechFilePath, buffer);
  
  console.log(`Orpheus Arabic speech generated: ${speechFilePath}`);
}

main().catch((error) => {
  console.error('Error generating Arabic speech:', error);
});
```

```
curl https://api.groq.com/openai/v1/audio/speech \
  -X POST \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "canopylabs/orpheus-arabic-saudi",
    "input": "مرحبا بكم في نموذج أورفيوس للتحويل من النص إلى الكلام. هذا مثال على جودة الصوت العربية السعودية الطبيعية.",
    "voice": "noura",
    "response_format": "wav"
  }' \
  --output orpheus-arabic.wav
```

## [Vocal Directions](#vocal-directions)

Orpheus V1 English supports **vocal directions** using bracketed text like `[cheerful]` or `[whisper]` to control how the model speaks. This powerful feature enables everything from subtle conversational nuances to highly expressive character performances.

### [How Directions Work](#how-directions-work)

* **More directions** \= more expressive, acted performance
* **Fewer/no directions** \= natural, casual conversational cadence
* Use 1-2 word directions (typically adjectives or adverbs)
  
**Common use cases:**

* **Customer support**: Use no directions for natural, friendly conversations
* **Game characters**: Add expressive directions for dynamic, performative speech
* **Professional narration**: Use `[professionally]` or `[authoritatively]` for business content
* **Storytelling**: Combine multiple directions to create engaging narrative performances

### [Direction Examples](#direction-examples)

**Conversational tones:**

* `[cheerful]`, `[friendly]`, `[casual]`, `[warm]`

**Professional styles:**

* `[professionally]`, `[authoritatively]`, `[formally]`, `[confidently]`

**Expressive performance:**

* `[whisper]`, `[excited]`, `[dramatic]`, `[deadpan]`, `[sarcastic]`

**Vocal qualities:**

* `[gravelly whisper]`, `[rapid babbling]`, `[singsong]`, `[breathy]`

**Note:** There isn't an official or exhaustive list of directions; the model recognizes many natural descriptors and ignores vague or unfamiliar ones.

## [Using Vocal Directions](#using-vocal-directions)

Natural ConversationExpressive PerformanceCombining Directions

### [Natural Conversation (No Directions)](#natural-conversation-no-directions)

For customer support, AI assistants, or natural dialogue, omit directions entirely. The model defaults to conversational, human-like cadence.

* **Example (Troy):** _"I see you ordered the Bose QuietComfort Ultra earbuds, order number 7829-XK-441, tracking ID H3J7L9C2F5V8, and yeah it looks like it's been stuck in transit since, uhh, Thursday the 8th."_
* **Example (Autumn):** _"Okay so I'm looking at your account here and it shows you've got the Dell XPS 15 9530, is that right? Let me just pull up the warranty info real quick... yep that all looks good!"_

**Tip:** Pure numbers like `203` are normalized to "two hundred and three." Use hyphens (`2-0-3`) for letter-by-letter reading.

### [Expressive Performance (With Directions)](#expressive-performance-with-directions)

Add bracketed directions for more dynamic, acted performances. Great for storytelling, game characters, or engaging content.

* _"**\[cheerful singsong\]** Good morning, everyone, and welcome to another beautiful day! **\[dropping tone\]** Now, let's talk about the budget cuts happening next month."_
* _"She picked up the phone and immediately started **\[rapid babbling\]** oh my god you won't believe what just happened I have to tell you everything right now."_
* _"**\[gravelly whisper\]** Legend has it that anyone who enters those woods after dark never comes back quite the same as they were before."_
* _"**\[piercing shout\]** Will someone please answer that phone it has been ringing nonstop **\[exasperated sigh\]** for the last twenty minutes straight!"_
* _"**\[mock sympathy\]** Oh no how terrible that must be for you **\[deadpan\]** anyway let me tell you about my actual problems this week."_

### [Combining Directions](#combining-directions)

You can use multiple directions in a single sentence to create dynamic performances:

* _"**\[building intensity\]** And then the car started making this noise, and the smoke was everywhere, and— **\[crescendo\]** the whole engine just exploded right there!"_
* _"**\[slurring slightly\]** I probably shouldn't have had that last glass of wine, but honestly— **\[giggling\]** this party is way more fun than I expected!"_
* _"The auctioneer rattled off **\[fast paced\]** fifty do I hear fifty-five fifty-five now sixty sixty going once going twice sold to the woman in red!"_

## [Available Voices](#available-voices)

### [English Voices](#english-voices)

The English model includes six professionally-trained voice personas. Each voice has different strengths for expressive direction performance.

| Voice Name | Voice ID | Gender |
| ---------- | -------- | ------ |
| Autumn     | autumn   | Female |
| Diana      | diana    | Female |
| Hannah     | hannah   | Female |
| Austin     | austin   | Male   |
| Daniel     | daniel   | Male   |
| Troy       | troy     | Male   |

  
**Note:** Some voices perform better with expressive directions than others. Experiment to find the voice that works best for your use case.

AutumnDianaHannahAustinDanielTroy

Autumn

0:000:00

Diana

0:000:00

Hannah

0:000:00

Austin

0:000:00

Daniel

0:000:00

Troy

0:000:00

### [Arabic Saudi Dialect Voices](#arabic-saudi-dialect-voices)

The Arabic model offers six distinct Saudi dialect voices with authentic pronunciation and regional nuances:

| Voice Name | Voice ID | Gender | Audio Sample |
| ---------- | -------- | ------ | ------------ |
| Abdullah   | abdullah | Male   | Coming soon  |
| Fahad      | fahad    | Male   | ✓            |
| Sultan     | sultan   | Male   | ✓            |
| Lulwa      | lulwa    | Female | ✓            |
| Noura      | noura    | Female | ✓            |
| Aisha      | aisha    | Female | Coming soon  |

FahadSultanLulwaNoura

Fahad

0:000:00

Sultan

0:000:00

Lulwa

0:000:00

Noura

0:000:00

## [Use Cases](#use-cases)

Customer SupportGame CharactersProfessional NarrationContent Creation

### [Customer Support & AI Assistants](#customer-support--ai-assistants)

Use **no directions** for natural, conversational interactions that feel human and approachable.

* _"I'm looking at your account here and everything seems to be in order. Let me just check that shipping status for you real quick."_

**Best for:** Customer service bots, virtual assistants, FAQ systems

### [Game Characters & Interactive Media](#game-characters--interactive-media)

Use **expressive directions** to create memorable, dynamic character performances.

* _"**\[menacing whisper\]** You shouldn't have come here... **\[dark chuckle\]** but now that you have, let's see what you're made of."_

**Best for:** Video games, interactive storytelling, virtual worlds

### [Professional Narration & Business Content](#professional-narration--business-content)

Use **subtle professional directions** for authoritative, polished delivery.

* _"**\[professionally\]** Welcome to our quarterly earnings call. Today we'll review our performance and outline strategic initiatives for the coming quarter."_

**Best for:** Corporate videos, e-learning, business presentations

### [Content Creation & Entertainment](#content-creation--entertainment)

Combine **multiple directions** for engaging, varied performances.

* _"**\[excited\]** So you won't believe what happened next! **\[building suspense\]** The door slowly creaked open and— **\[dramatic gasp\]** there it was!"_

**Best for:** Podcasts, audiobooks, YouTube content, storytelling

## [Best Practices](#best-practices)

**Punctuation control:** Experiment with removing punctuation to give the model more freedom in choosing intonation patterns, especially for expressive performances.

**Voice selection:** Test different voices for your use case; some handle expressive directions better than others, particularly for complex emotional ranges.

**Arabic considerations:** Use proper Arabic script with diacritical marks. Test pronunciation with sample content before production deployment.

## [Limitations](#limitations)

**Input length:** The input text length is limited to 200 characters.

**Batch processing:** The [batch processing API](https://console.groq.com/docs/batch) is not supported at this time for Orpheus models.


