import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adiciona o diretório pai ao caminho para conseguir importar o main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa as funções que queremos testar do seu backend
from main import create_session, get_user_by_cpf, UserProfile

class TestBackendUnitario(unittest.TestCase):

    @patch('main.redis_client') # "Finge" o Redis
    def test_create_session(self, mock_redis):
        """
        Teste: Verificar se create_session gera um ID e salva no Redis.
        """
        # Configuração
        cpf_teste = "12345678900"
        
        # Execução
        session_id = create_session(cpf_teste)
        
        # Verificações (Asserts)
        self.assertIsInstance(session_id, str) # O ID deve ser uma string
        self.assertTrue(len(session_id) > 0)   # O ID não pode ser vazio
        
        # Verifica se o código chamou o comando .set() do Redis
        # Isso prova que a função tentou salvar a sessão
        mock_redis.set.assert_called_once() 

    @patch('main.redis_client')
    def test_get_user_exists(self, mock_redis):
        """
        Teste: Verificar se get_user_by_cpf retorna os dados corretamente quando o usuário existe.
        """
        # Configuração: Dizemos ao Redis falso o que ele deve responder
        mock_redis.get.return_value = '{"nome": "Teste Silva", "cpf": "111"}'
        
        # Execução
        usuario = get_user_by_cpf("111")
        
        # Verificação
        self.assertEqual(usuario['nome'], "Teste Silva")

    @patch('main.redis_client')
    def test_get_user_not_exists(self, mock_redis):
        """
        Teste: Verificar se retorna None quando o usuário não existe.
        """
        # Configuração: Redis responde None (nulo)
        mock_redis.get.return_value = None
        
        # Execução
        usuario = get_user_by_cpf("999999")
        
        # Verificação
        self.assertIsNone(usuario)

if __name__ == '__main__':
    unittest.main()