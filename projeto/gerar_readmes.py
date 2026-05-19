import os

def gerar_readmes():
    # Caminho da pasta atual onde o script está sendo executado
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    print("Iniciando a geração de READMEs...")
    
    for root, dirs, files in os.walk(diretorio_atual):
        # Ignora pastas de ambiente virtual, git e cache para não poluir o projeto
        pastas_ignorar = ['.git', 'venv', '.venv', '__pycache__', 'egg-info', '.pytest_cache']
        if any(p in root for p in pastas_ignorar):
            continue
            
        for file in files:
            # Foca apenas em arquivos Python (exceto o inicializador do módulo)
            if file.endswith('.py') and file != '__init__.py' and file != 'gerar_readmes.py':
                
                # Define o nome do README baseado no nome do arquivo original
                nome_sem_extensao = file.replace('.py', '')
                readme_name = f'README_{nome_sem_extensao}.md'
                readme_path = os.path.join(root, readme_name)
                
                # Só cria o arquivo se ele ainda não existir (evita sobrescrever seu trabalho)
                if not os.path.exists(readme_path):
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f'# Documentação de `{file}`\n\n')
                        f.write('## 📝 Descrição\n')
                        f.write(f'Este arquivo faz parte do projeto Flask e contém as regras de negócio de `{nome_sem_extensao}`.\n\n')
                        f.write('- [ ] Adicione aqui a explicação do que este arquivo faz.\n\n')
                        f.write('## 🛠️ Dependências e Rotas\n')
                        f.write('Principais funções, classes ou rotas Flask mapeadas neste arquivo.\n')
                    
                    # Mostra o caminho relativo no terminal para você acompanhar
                    caminho_relativo = os.path.relpath(readme_path, diretorio_atual)
                    print(f'✅ Criado: {caminho_relativo}')

    print("\nProcesso concluído! Agora é só preencher os detalhes.")

if __name__ == '__main__':
    gerar_readmes()