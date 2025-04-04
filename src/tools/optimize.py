import os
from PIL import Image
import imageio
import fitz


class FileOptimizer:
    video_formats = ['.mp4', '.avi', '.mkv', '.mov']
    image_formats = ['.jpg', '.jpeg', '.png', '.gif']
    document_formats = ['.doc', '.docx', '.pdf']

    @staticmethod
    def is_format_supported(file_format: str):
        file_format = file_format.lower()
        if file_format in FileOptimizer.image_formats:
            return True
        if file_format in FileOptimizer.video_formats:
            return True
        if file_format == '.pdf':
            return True
        return False

    @staticmethod
    def determine_video_parameters(input_path):
        """
        Определяет параметры для оптимизации видео на основе разрешения.
        """
        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        resolution = meta.get('size', (640, 480))
        width, height = resolution
        reader.close()

        if width >= 1920 or height >= 1080:
            crf = '28'
            preset = 'slow'
        elif width >= 1280 or height >= 720:
            crf = '23'
            preset = 'medium'
        else:
            crf = '18'
            preset = 'fast'
        return crf, preset

    @staticmethod
    async def optimize_image(input_path, output_path):
        """
        Оптимизация изображений
        """
        ext = os.path.splitext(input_path)[1].lower()
        with Image.open(input_path) as img:
            if ext in ['.jpg', '.jpeg']:
                img.save(output_path, 'JPEG', optimize=True, quality=95)
            elif ext == '.png':
                img.save(output_path, 'PNG', optimize=True)
            elif ext == '.gif':
                img.save(output_path, 'GIF', optimize=True)
            else:
                raise ValueError("Неподдерживаемый формат изображения.")
        return output_path

    @classmethod
    async def optimize_video(cls, input_path, output_path, crf=None, preset=None):
        """
        Оптимизация видео.
        Если параметры crf или preset не заданы, они определяются автоматически.
        """
        if crf is None or preset is None:
            crf, preset = cls.determine_video_parameters(input_path)

        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        fps = meta.get('fps', 25)

        writer = imageio.get_writer(
            output_path, fps=fps, codec='libx264',
            ffmpeg_params=['-crf', crf, '-preset', preset]
        )

        for frame in reader:
            writer.append_data(frame)

        writer.close()
        reader.close()
        return output_path

    @staticmethod
    async def optimize_pdf(input_path, output_path):
        """
        Оптимизация PDF.
        """
        doc = fitz.open(input_path)
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return output_path

    @classmethod
    async def optimize_file(cls, input_path, output_path=None, **kwargs):
        """
        Универсальная функция оптимизации файла.
        Определяет тип файла по расширению и вызывает соответствующий метод.
        """
        ext = os.path.splitext(input_path)[1].lower()
        if output_path is None:
            base, ext_part = os.path.splitext(input_path)
            output_path = base + '_optimized' + ext_part

        if ext in cls.image_formats:
            return await cls.optimize_image(input_path, output_path)
        elif ext in cls.video_formats:
            return await cls.optimize_video(input_path, output_path, crf=kwargs.get('crf'), preset=kwargs.get('preset'))
        elif ext in cls.document_formats:
            if ext == '.pdf':
                return await cls.optimize_pdf(input_path, output_path)
            else:
                raise NotImplementedError(f"Оптимизация для файлов формата {ext} не реализована.")
        else:
            raise ValueError("Формат файла не поддерживается для оптимизации.")
