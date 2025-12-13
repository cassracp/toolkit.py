# features/token_generator.py
import secrets

class TokenGeneratorFeature:
    def generate_token(self, nbytes: int = 32) -> str:
        """
        Gera um token de segurança aleatório e seguro para URLs.

        Args:
            nbytes: O número de bytes de aleatoriedade para o token.
                    Um número maior de bytes resulta em um token mais seguro e mais longo.
                    O padrão é 32 bytes, que é uma escolha segura para a maioria dos casos de uso.

        Returns:
            Uma string contendo o token seguro.
        """
        return secrets.token_urlsafe(nbytes)

    def run(self):
        print("\n" + "=" * 50)
        print("         GERADOR DE TOKEN CRIPTOGRAFICAMENTE SEGURO")
        print("=" * 50)
        
        while True:
            nbytes_input = input(
                "Digite o número de bytes para o token (padrão: 32 para 256 bits de entropia, 43 caracteres Base64) ou 'q' para voltar: "
            )
            if nbytes_input.lower() == 'q':
                break
            
            try:
                nbytes = int(nbytes_input) if nbytes_input else 32
                if nbytes <= 0:
                    print("Por favor, digite um número inteiro positivo para os bytes.")
                    continue
                token = self.generate_token(nbytes)
                print(f"\nToken Gerado ({nbytes} bytes): {token}")
                print("-" * 50)
                input("Pressione Enter para gerar outro token ou 'q' para voltar...")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número inteiro.")
            except Exception as e:
                print(f"Ocorreu um erro inesperado: {e}")
            
