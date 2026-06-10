# -*- coding: utf-8 -*-
import os
import json

class UserConfigManager:
    """
    Gerenciador das configurações particulares do usuário.
    Lê e escreve em um arquivo user_config.json na raiz do projeto.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Calcula o caminho da raiz do projeto (um nível acima de toolkit/)
            self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_file = os.path.join(self.root_dir, 'user_config.json')
            self.config_data = {}
            self._load_config()
            self.initialized = True

    def _load_config(self):
        """Carrega o JSON. Se não existir, cria com dados vazios."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"AVISO: Falha ao ler {self.config_file}: {e}")
                self.config_data = {}
        else:
            self._save_config()

    def _save_config(self):
        """Salva os dados no JSON."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"AVISO: Falha ao gravar {self.config_file}: {e}")

    def get(self, key, default_value=None):
        """Retorna uma configuração. Se não existir, retorna default_value."""
        return self.config_data.get(key, default_value)

    def set(self, key, value):
        """Define uma configuração e salva o arquivo."""
        self.config_data[key] = value
        self._save_config()
