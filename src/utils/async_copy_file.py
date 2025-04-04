import aiofiles


async def async_copy_file(src: str, dst: str):
    """
    Асинхронное копирование файла с использованием aiofiles.
    """
    async with aiofiles.open(src, 'rb') as frb:
        async with aiofiles.open(dst, 'wb') as fwb:
            while True:
                data = await frb.read(1024 * 1024)
                if not data:
                    break
                await fwb.write(data)
