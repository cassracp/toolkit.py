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
        return "Conversor de imagens (múltiplas) para o formato .webp"

    def run(self):
        """
        Executa o processo de conversão de imagem com diálogos de arquivo.
        """
        print(f"--- {self} ---")
        try:
            input_paths = self._select_input_file()
            if not input_paths:
                print("Nenhum arquivo de entrada selecionado. Operação cancelada.")
                return

            # Use o diretório do primeiro arquivo selecionado como diretório inicial para o diálogo de saída
            initial_dir = os.path.dirname(input_paths[0]) if input_paths else None
            output_dir = self._select_output_directory(initial_dir)
            if not output_dir:
                print("Nenhum diretório de saída selecionado. Operação cancelada.")
                return

            quality = self._get_quality()

            for input_path in input_paths:
                try:
                    # Constrói o caminho de saída para cada imagem no diretório selecionado
                    base_name = os.path.splitext(os.path.basename(input_path))[0]
                    output_path = os.path.join(output_dir, base_name + ".webp")

                    self._convert_image(input_path, output_path, quality)
                    print(f"'{os.path.basename(input_path)}' convertido com sucesso para: '{output_path}'")
                except Exception as e:
                    print(f"Erro ao converter '{os.path.basename(input_path)}': {e}")

            print("\nTodas as operações de conversão foram concluídas.")

        except Exception as e:
            print(f"Ocorreu um erro geral durante a conversão: {e}")

    def _select_input_file(self):
        """
        Abre um diálogo para o usuário selecionar o arquivo de imagem de entrada.
        """
        print("Por favor, selecione o arquivo de imagem a ser convertido.")
        input_paths = filedialog.askopenfilenames(
            title="Selecione a imagem para converter",
            filetypes=self.supported_formats
        )
        return input_paths

    def _select_output_directory(self, initial_dir=None):
        """
        Abre um diálogo para o usuário selecionar um diretório para salvar os arquivos WebP de saída.
        """
        print("Por favor, selecione o diretório onde os arquivos WebP serão salvos.")
        output_dir = filedialog.askdirectory(
            title="Selecione o diretório de saída",
            initialdir=initial_dir
        )
        return output_dir

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
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "webp", quality=quality)

if __name__ == '__main__':
    # Teste rápido
    converter = ImageConverter()
    converter.run()
