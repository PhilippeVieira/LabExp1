import csv
import requests
from datetime import datetime

# Carregar o token de acesso do GitHub a partir de variáveis de ambiente
GITHUB_TOKEN = "" # TOKEN de acesso
GITHUB_API_URL = "https://api.github.com/graphql"

# Query GraphQL para obter os repositórios mais populares
QUERY = """
query ($cursor: String) {
  search(query: "stars:>1000", type: REPOSITORY, first: 20, after: $cursor) {
    pageInfo {
      endCursor
      hasNextPage
    }
    edges {
      node {
        ... on Repository {
          name
          owner {
            login
          }
          createdAt
          updatedAt
          primaryLanguage {
            name
          }
          releases {
            totalCount
          }
          pullRequests(states: MERGED) {
            totalCount
          }
          issues(states: [CLOSED]) {
            totalCount
          }
          totalIssues: issues {
            totalCount
          }
          stargazerCount
        }
      }
    }
  }
}
"""

def fetch_github_data():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    repos = []
    cursor = None

    while True:
        response = requests.post(GITHUB_API_URL, json={"query": QUERY, "variables": {"cursor": cursor}}, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro: {response.status_code}, {response.text}")
            return None
        
        data = response.json()
        search_data = data.get("data", {}).get("search", {})
        
        if not search_data:
            break
        
        repos.extend(search_data.get("edges", []))
        cursor = search_data.get("pageInfo", {}).get("endCursor")
        
        if not search_data.get("pageInfo", {}).get("hasNextPage"):
            break
    
    return repos

def process_data(edges):
    repos = []
    for edge in edges:
        repo = edge["node"]
        created_at = datetime.strptime(repo["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
        updated_at = datetime.strptime(repo["updatedAt"], "%Y-%m-%dT%H:%M:%SZ")
        
        repos.append({
            "name": repo["name"], # nome do repositório
            "owner": repo["owner"]["login"], # Dono do repositório
            "age_years": (datetime.utcnow() - created_at).days // 365, # RQ 01: Idade do repositório
            "time_since_last_update": (datetime.utcnow() - updated_at).days, # RQ 04: Tempo até a última atualização
            "language": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else "Unknown", # RQ 05: Linguagem primária
            "releases": repo["releases"]["totalCount"], # RQ 03: Total de releases
            "pull_requests": repo["pullRequests"]["totalCount"], # RQ 02: Total de pull requests aceitas
            "closed_issues": repo["issues"]["totalCount"], # Issues fechadas
            "total_issues": repo["totalIssues"]["totalCount"], # Total de issues
            "issue_closure_rate": repo["issues"]["totalCount"] / repo["totalIssues"]["totalCount"] if repo["totalIssues"]["totalCount"] > 0 else 0, # RQ 06: Percentual de issues fechadas
            "stars": repo["stargazerCount"] # Total de estrelas
        })
    return repos

if __name__ == "__main__":
    edges = fetch_github_data()
    if edges:
        repos = process_data(edges)
        
        # Criar e escrever no arquivo CSV
        with open("github_repos_data.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Escrever o cabeçalho do CSV
            writer.writerow(["Nome", "Dono", "Idade (anos)", "Dias desde última atualização",
                             "Linguagem", "Releases", "Pull Requests", "Issues Fechadas",
                             "Total Issues", "Taxa de Fechamento de Issues", "Stars"])
            
            # Escrever os dados de cada repositório
            for repo in repos:
                writer.writerow([
                    repo["name"], repo["owner"], repo["age_years"],
                    repo["time_since_last_update"], repo["language"],
                    repo["releases"], repo["pull_requests"], repo["closed_issues"],
                    repo["total_issues"], repo["issue_closure_rate"], repo["stars"],
                ])

        print("Dados salvos em github_repos_data.csv")
