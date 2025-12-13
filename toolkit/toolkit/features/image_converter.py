from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog

class ImageConverter:
    """
    Converte imagens para o formato WebP.
    """
    def __init__(self):
        self.supported_formats = [
            ("Imagens Suportadas", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("PNG", "*.png"),
            ("Bitmap", "*.bmp"),
            ("TIFF", "*.tiff"),
            ("All files", "*.*")
        ]
        self.root = tk.Tk()
        self.root.withdraw()  # Oculta a janela principal do Tkinter

    def __str__(self):
        return "Conversor de imagens para o formato .webp"

    def run(self):
        """
        Executa o processo de conversão de imagem com diálogos de arquivo.
        """
        print(f"--- {self} ---")
        try:
            input_path = self._select_input_file()
            if not input_path:
                print("Nenhum arquivo de entrada selecionado. Operação cancelada.")
                return

            output_path = self._select_output_file(input_path)
            if not output_path:
                print("Nenhum local de saída selecionado. Operação cancelada.")
                return

            quality = self._get_quality()

            self._convert_image(input_path, output_path, quality)

            print(f"\nImagem convertida com sucesso para: {output_path}")

        except Exception as e:
            print(f"Ocorreu um erro durante a conversão: {e}")

    def _select_input_file(self):
        """
        Abre um diálogo para o usuário selecionar o arquivo de imagem de entrada.
        """
        print("Por favor, selecione o arquivo de imagem a ser convertido.")
        input_path = filedialog.askopenfilename(
            title="Selecione a imagem para converter",
            filetypes=self.supported_formats
        )
        return input_path

    def _select_output_file(self, input_path):
        """
        Abre um diálogo para o usuário definir o local e nome do arquivo de saída.
        """
        print("Por favor, defina o nome e o local para o arquivo .webp de saída.")
        # Define o nome do arquivo de saída padrão
        default_name = os.path.splitext(os.path.basename(input_path))[0] + ".webp"
        # Define o diretório inicial como o mesmo do arquivo de entrada
        initial_dir = os.path.dirname(input_path)
        
        output_path = filedialog.asksaveasfilename(
            title="Salvar arquivo WebP como...",
            initialdir=initial_dir,
            initialfile=default_name,
            defaultextension=".webp",
            filetypes=[("WebP", "*.webp")]
        )
        return output_path

    def _get_quality(self):
        """
        Solicita e valida a qualidade da imagem WebP.
        """
        while True:
            try:
                quality_str = input("Insira a qualidade da imagem WebP (1-100, padrão 80): ")
                if not quality_str:
                    return 80
                quality = int(quality_str)
                if 1 <= quality <= 100:
                    return quality
                else:
                    print("Por favor, insira um valor entre 1 e 100.")
            except ValueError:
                print("Entrada inválida. Por favor, insira um número.")

    def _convert_image(self, input_path, output_path, quality):
        """
        Converte a imagem para WebP usando a biblioteca Pillow.
        """
        with Image.open(input_path) as img:
            # Garante que a imagem não tenha canal de transparência se o formato de saída não suportar
            if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                 if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
            img.save(output_path, "webp", quality=quality)

if __name__ == '__main__':
    # Teste rápido
    converter = ImageConverter()
    converter.run()
