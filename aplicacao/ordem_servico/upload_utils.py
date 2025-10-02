# ordem_servico/upload_utils.py

import os
import uuid
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import boto3
from botocore.exceptions import NoCredentialsError
from flask import current_app

class UploadManager:
    """Gerenciador de uploads de arquivos para ordens de serviço"""
    
    # Extensões permitidas
    ALLOWED_EXTENSIONS = {
        'imagem': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'},
        'documento': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'},
        'todos': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
    }
    
    # Tamanho máximo: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, upload_folder=None):
        self.upload_folder = upload_folder or os.path.join(current_app.static_folder, 'uploads', 'os')
        self.ensure_upload_folder()
    
    def ensure_upload_folder(self):
        """Garante que o diretório de upload existe"""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename, tipo='todos'):
        """Verifica se a extensão do arquivo é permitida"""
        if not filename or '.' not in filename:
            return False
        
        extensao = filename.rsplit('.', 1)[1].lower()
        return extensao in self.ALLOWED_EXTENSIONS.get(tipo, self.ALLOWED_EXTENSIONS['todos'])
    
    def validate_file(self, file, tipo='todos'):
        """Valida arquivo antes do upload"""
        errors = []
        
        # Verifica se arquivo foi selecionado
        if not file or file.filename == '':
            errors.append('Nenhum arquivo foi selecionado')
            return errors
        
        # Verifica extensão
        if not self.is_allowed_file(file.filename, tipo):
            extensoes = ', '.join(self.ALLOWED_EXTENSIONS[tipo])
            errors.append(f'Tipo de arquivo não permitido. Permitidos: {extensoes}')
        
        # Verifica tamanho (se possível)
        try:
            file.seek(0, 2)  # Vai para o final do arquivo
            size = file.tell()
            file.seek(0)  # Volta para o início
            
            if size > self.MAX_FILE_SIZE:
                errors.append(f'Arquivo muito grande. Máximo: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB')
        except:
            pass  # Se não conseguir verificar o tamanho, continua
        
        return errors
    
    def generate_unique_filename(self, original_filename):
        """Gera nome único para o arquivo"""
        # Pega apenas a extensão do arquivo original
        ext = os.path.splitext(original_filename)[1].lower()
        
        # Gera nome único usando UUID e timestamp
        unique_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{ext}"
        
        return unique_name
    
    def save_file_local(self, file, os_id, categoria='documento'):
        """Salva arquivo localmente"""
        try:
            # Cria diretório específico para a OS
            os_folder = os.path.join(self.upload_folder, str(os_id))
            if not os.path.exists(os_folder):
                os.makedirs(os_folder, exist_ok=True)
            
            # Gera nome único
            unique_filename = self.generate_unique_filename(file.filename)
            file_path = os.path.join(os_folder, unique_filename)
            
            # Salva o arquivo
            file.save(file_path)
            
            # Pega informações do arquivo
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0]
            
            # Se for imagem, cria thumbnail
            if self.is_image_file(file_path):
                self.create_thumbnail(file_path, os_folder)
            
            return {
                'success': True,
                'nome_arquivo': unique_filename,
                'caminho_local': file_path,
                'tamanho': file_size,
                'tipo_arquivo': mime_type or 'application/octet-stream',
                'url_relativa': f"/static/uploads/os/{os_id}/{unique_filename}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao salvar arquivo: {str(e)}'
            }
    
    def is_image_file(self, file_path):
        """Verifica se o arquivo é uma imagem"""
        try:
            with Image.open(file_path) as img:
                return True
        except:
            return False
    
    def create_thumbnail(self, image_path, output_folder, size=(200, 200)):
        """Cria thumbnail de uma imagem"""
        try:
            with Image.open(image_path) as img:
                # Mantém proporção
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Nome do thumbnail
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                thumb_filename = f"{name}_thumb{ext}"
                thumb_path = os.path.join(output_folder, thumb_filename)
                
                # Salva thumbnail
                img.save(thumb_path, optimize=True, quality=85)
                
                return thumb_path
        except Exception as e:
            print(f"Erro ao criar thumbnail: {e}")
            return None
    
    def delete_file_local(self, file_path):
        """Remove arquivo do sistema local"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Remove thumbnail se existir
                folder = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)
                thumb_path = os.path.join(folder, f"{name}_thumb{ext}")
                
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                
                return True
        except Exception as e:
            print(f"Erro ao remover arquivo: {e}")
            return False
    
    def upload_to_s3(self, file_path, bucket_name, object_name=None):
        """
        Upload arquivo para S3 (opcional)
        Requer configuração das credenciais AWS
        """
        try:
            if object_name is None:
                object_name = os.path.basename(file_path)
            
            s3_client = boto3.client('s3')
            s3_client.upload_file(file_path, bucket_name, object_name)
            
            # Gera URL pública
            url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
            
            return {
                'success': True,
                'url': url,
                'bucket': bucket_name,
                'key': object_name
            }
            
        except NoCredentialsError:
            return {
                'success': False,
                'error': 'Credenciais AWS não configuradas'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro no upload S3: {str(e)}'
            }
    
    def get_file_info(self, file_path):
        """Retorna informações sobre um arquivo"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            mime_type = mimetypes.guess_type(file_path)[0]
            
            return {
                'tamanho': stat.st_size,
                'tipo_arquivo': mime_type or 'application/octet-stream',
                'data_modificacao': datetime.fromtimestamp(stat.st_mtime),
                'exists': True
            }
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }


# Funções auxiliares
def allowed_file(filename, tipo='todos'):
    """Função auxiliar para verificar extensão permitida"""
    manager = UploadManager()
    return manager.is_allowed_file(filename, tipo)

def format_file_size(size_bytes):
    """Formata tamanho do arquivo"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
