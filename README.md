# lion-perplexity

```
lion_perplexity/
├── lion_perplexity/
│   ├── __init__.py
│   ├── api_endpoints/
│   │   ├── __init__.py
│   │   ├── api_request.py  # Base request handling
│   │   ├── data_models.py  # Base request/response models
│   │   └── chat_completions/
│   │       ├── __init__.py
│   │       ├── request/
│   │       │   ├── __init__.py
│   │       │   ├── message_models.py
│   │       │   └── request_body.py
│   │       └── response/
│   │           ├── __init__.py
│   │           ├── choice_models.py
│   │           ├── response_body.py
│   │           └── usage_models.py
│   ├── perplexity_model.py  # Model implementation
│   └── perplexity_service.py  # Service implementation
├── tests/
└── pyproject.toml
```