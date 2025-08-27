# Python AI Search with Azure OpenAI and Azure AI Search on Azure App Service

This project demonstrates retrieval augmented generation (RAG) using FastAPI, Azure OpenAI, and Azure AI Search, deployed to Azure App Service, and secured with passwordless authentication through managed identities. For a comprehensive tutorial that shows how to use this sample, see [Tutorial: Build a Retrieval Augmented Generation with Azure OpenAI and Azure AI Search (FastAPI)](https://learn.microsoft.com/azure/app-service/tutorial-ai-openai-search-python).

## Features

- **FastAPI** web application with a chat interface using Thymeleaf templates.
- **RAG implementation** using Azure App Service, Azure OpenAI, and Azure AI Search.
- **Hybrid search** combining vector search, keyword matching, and semantic ranking.
- **Citation display** showing the sources of information in responses.
- **Enterprise-ready security** with managed identities and RBAC role assignments.
- **Zero trust configuration** supporting Azure OpenAI on Your Data best practices.

## Hybrid Search Implementation

This application leverages Azure AI Search's hybrid search capabilities to provide more relevant and accurate results:

- **Vector search**: Uses embedding models to convert text into vector representations, enabling similarity search based on meaning rather than keywords.
   
- **Keyword matching**: Traditional keyword-based search to capture exact matches and specific terms.
   
- **Semantic ranking**: Advanced AI-powered re-ranking that improves search relevance by understanding the semantic meaning of queries and documents.

The combination of these approaches ensures the most relevant information is retrieved before being passed to the Azure OpenAI service for generating responses, providing more accurate, contextually aware answers with proper citations.

## Azure Resources

The application requires the following Azure resources:

- **Azure App Service**: Hosts the Spring Boot web application.
- **Azure OpenAI**: Provides GPT model for chat completions and embedding model for vectorization.
- **Azure AI Search**: Provides vector search and semantic ranking capabilities.
- **Azure Storage Account**: Stores documents and document chunks.

## Get started

### Environment Setup

To create a conda environment for this project:

```bash
# Create a new conda environment
conda create -n cube-rag-service python=3.11

# Activate the environment
conda activate cube-rag-service

# Install dependencies (if requirements.txt exists)
pip install -r requirements.txt
```

#### Install Azure Developer CLI (azd)

For macOS:
```bash
# Using Homebrew
brew install azure-dev

# Or using curl
curl -fsSL https://aka.ms/install-azd.sh | bash
```

For Windows:
```bash
# Using winget
winget install Microsoft.AzureDeveloperCLI

# Or using PowerShell
powershell -ex AllSigned -c "Invoke-RestMethod 'https://aka.ms/install-azd.ps1' | Invoke-Expression"
```

For Linux:
```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

After installation, authenticate with Azure:
```bash
azd auth login
```

See [Tutorial: Build a Retrieval Augmented Generation with Azure OpenAI and Azure AI Search (FastAPI)](https://learn.microsoft.com/azure/app-service/tutorial-ai-openai-search-python).

## Role Assignments

The following RBAC role assignments are needed to enable secure service-to-service communication:

| Role Assignment | Assignee | Target Resource | Purpose |
|-----------------|----------|----------------|---------|
| Cognitive Services OpenAI User | App Service | Azure OpenAI | Allows the web application to call the Azure OpenAI service for chat completions. |
| Search Index Data Reader | Azure OpenAI | Azure AI Search | Enables the OpenAI service to query data from the search index during inference. |
| Search Service Contributor | Azure OpenAI | Azure AI Search | Allows the OpenAI service to query the index schema for auto fields mapping. |
| Storage Blob Data Contributor | Azure OpenAI | Storage Account | Allows OpenAI to read from the input container and write preprocessed results. |
| Cognitive Services OpenAI Contributor | Azure AI Search | Azure OpenAI | Enables the Azure AI Search service to access Azure OpenAI's embedding endpoint. |
| Storage Blob Data Reader | Azure AI Search | Storage Account | Allows Azure AI Search to read document blobs and chunk blobs. |

## Contributing

make sure you set your environment varoables for germanywestcentral
# azd env set AZURE_LOCATION germanywestcentral

