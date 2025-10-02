# os_calculos.py - Módulo de Cálculos para Ordem de Serviço
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta

class CalculadoraOS:
    """Classe responsável por todos os cálculos da Ordem de Serviço"""
    
    @staticmethod
    def validar_dados_os(dados):
        """
        Valida os dados da OS antes dos cálculos
        Args:
            dados (dict): Dados da OS
        Returns:
            tuple: (bool, lista_erros)
        """
        erros = []
        
        # Validações obrigatórias - DEBUG CLIENTE
        cliente_id = dados.get('cliente_id')
        print(f"=== DEBUG VALIDAÇÃO CLIENTE ===")
        print(f"cliente_id raw: '{cliente_id}'")
        print(f"tipo: {type(cliente_id)}")
        print(f"bool(cliente_id): {bool(cliente_id)}")
        print(f"cliente_id == 'None': {cliente_id == 'None'}")
        print(f"cliente_id == '': {cliente_id == ''}")
        
        # Validação mais robusta para cliente
        print(f"=== ANÁLISE DETALHADA DO CLIENTE ===")
        print(f"dados keys: {list(dados.keys())}")
        print(f"'cliente_id' in dados: {'cliente_id' in dados}")
        
        if not cliente_id or cliente_id == 'None' or cliente_id == '' or str(cliente_id).strip() == '':
            erros.append('Cliente é obrigatório')
        
        if not dados.get('data_emissao'):
            erros.append('Data de emissão é obrigatória')
        
        # Validar horas se informadas
        hora_inicio = dados.get('hora_inicio')
        hora_termino = dados.get('hora_termino')
        
        if hora_inicio and hora_termino:
            try:
                datetime.strptime(hora_inicio, '%H:%M')
                datetime.strptime(hora_termino, '%H:%M')
            except ValueError:
                erros.append('Formato de hora inválido (use HH:MM)')
        
        # Validar quilometragem
        km_inicial = dados.get('km_inicial')
        km_final = dados.get('km_final')
        
        if km_inicial is not None and km_final is not None:
            try:
                km_i = float(km_inicial)
                km_f = float(km_final)
                if km_f < km_i:
                    erros.append('KM final deve ser maior que KM inicial')
            except ValueError:
                erros.append('Valores de quilometragem devem ser numéricos')
        
        return len(erros) == 0, erros
    
    # Tabela de referência para deslocamento
    TABELA_DESLOCAMENTO = [
        (10, 25), (20, 44), (30, 66), (40, 88), (50, 110),
        (60, 132), (70, 154), (80, 176), (90, 198), (100, 220),
        (110, 242), (120, 264), (130, 286), (140, 308), (150, 330)
    ]
    
    @staticmethod
    def calcular_horas_trabalhadas(hora_inicio, hora_termino):
        """
        Calcula o total de horas trabalhadas
        Args:
            hora_inicio (str): Hora no formato HH:MM
            hora_termino (str): Hora no formato HH:MM
        Returns:
            float: Total de horas em decimal
        """
        if not hora_inicio or not hora_termino:
            return 0.0
            
        try:
            # Converter strings para datetime
            inicio = datetime.strptime(hora_inicio, '%H:%M')
            termino = datetime.strptime(hora_termino, '%H:%M')
            
            # Se término for menor que início, assumir que passou da meia-noite
            if termino < inicio:
                termino += timedelta(days=1)
            
            # Calcular diferença
            diff = termino - inicio
            horas = diff.total_seconds() / 3600
            
            return round(horas, 2)
        except ValueError:
            return 0.0
    
    @staticmethod
    def calcular_km_total(km_inicial, km_final):
        """
        Calcula o total de quilômetros percorridos
        Args:
            km_inicial (float): Quilometragem inicial
            km_final (float): Quilometragem final
        Returns:
            float: Total de quilômetros
        """
        if not km_inicial or not km_final:
            return 0.0
            
        try:
            inicial = float(km_inicial)
            final = float(km_final)
            
            if final >= inicial:
                return round(final - inicial, 1)
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calcular_valor_deslocamento(km_total):
        """
        Calcula o valor do deslocamento - só cobra se > 50km
        Args:
            km_total (float): Total de quilômetros
        Returns:
            float: Valor do deslocamento
        """
        if not km_total or km_total <= 50:
            return 0.0
            
        km = float(km_total)
        valor_por_km = 1.50  # R$ 1,50 por km
        
        return km * valor_por_km
    
    @staticmethod
    def calcular_valor_servicos(servicos_data, horas_trabalhadas=0):
        """
        Calcula o valor total dos serviços
        Args:
            servicos_data (list): Lista de serviços com quantidade e valor_unitario
            horas_trabalhadas (float): Total de horas trabalhadas (não usado no cálculo)
        Returns:
            float: Valor total dos serviços
        """
        if not servicos_data:
            return 0.0
            
        valor_total = 0.0
        
        for servico in servicos_data:
            quantidade = float(servico.get('quantidade', 0))
            valor_unitario = float(servico.get('valor_unitario', 0))
            
            # Valor = quantidade * valor_unitario (sem multiplicar por horas)
            valor_servico = quantidade * valor_unitario
            valor_total += valor_servico
        
        return round(valor_total, 2)
    
    @staticmethod
    def calcular_valor_produtos(produtos_data):
        """
        Calcula o valor total dos produtos
        Args:
            produtos_data (list): Lista de produtos com quantidade e valor_unitario
        Returns:
            float: Valor total dos produtos
        """
        if not produtos_data:
            return 0.0
            
        valor_total = 0.0
        
        for produto in produtos_data:
            quantidade = float(produto.get('quantidade', 0))
            valor_unitario = float(produto.get('valor_unitario', 0))
            
            # Valor = quantidade * valor_unitario
            valor_produto = quantidade * valor_unitario
            valor_total += valor_produto
        
        return round(valor_total, 2)
    
    @staticmethod
    def calcular_valor_total(valor_servicos, valor_produtos, valor_deslocamento):
        """
        Calcula o valor total da OS
        Args:
            valor_servicos (float): Valor dos serviços
            valor_produtos (float): Valor dos produtos
            valor_deslocamento (float): Valor do deslocamento
        Returns:
            float: Valor total da OS
        """
        servicos = float(valor_servicos or 0)
        produtos = float(valor_produtos or 0)
        deslocamento = float(valor_deslocamento or 0)
        
        return round(servicos + produtos + deslocamento, 2)
    
    @staticmethod
    def calcular_todos_valores(dados_form, servicos_data=None, produtos_data=None):
        """
        Calcula todos os valores da OS de uma vez
        Args:
            dados_form (dict): Dados do formulário
            servicos_data (list): Lista de serviços
            produtos_data (list): Lista de produtos
        Returns:
            dict: Dicionário com todos os valores calculados
        """
        # Calcular horas trabalhadas
        horas_trabalhadas = CalculadoraOS.calcular_horas_trabalhadas(
            dados_form.get('hora_inicio'),
            dados_form.get('hora_termino')
        )
        
        # Calcular KM total
        km_total = CalculadoraOS.calcular_km_total(
            dados_form.get('km_inicial'),
            dados_form.get('km_final')
        )
        
        # Calcular valor do deslocamento
        valor_deslocamento = CalculadoraOS.calcular_valor_deslocamento(km_total)
        
        # Calcular valor dos serviços
        valor_servicos = CalculadoraOS.calcular_valor_servicos(
            servicos_data or [],
            horas_trabalhadas
        )
        
        # Calcular valor dos produtos
        valor_produtos = CalculadoraOS.calcular_valor_produtos(produtos_data or [])
        
        # Calcular valor total
        valor_total = CalculadoraOS.calcular_valor_total(
            valor_servicos,
            valor_produtos,
            valor_deslocamento
        )
        
        return {
            'total_horas': horas_trabalhadas,
            'km_total': km_total,
            'valor_deslocamento': valor_deslocamento,
            'valor_servicos': valor_servicos,
            'valor_produtos': valor_produtos,
            'valor_total': valor_total
        }
    
    @staticmethod
    def calcular_parcelas(valor_total, quantidade_parcelas, primeira_data=None):
        """
        Calcula as parcelas para pagamento
        Args:
            valor_total (float): Valor total da OS
            quantidade_parcelas (int): Número de parcelas
            primeira_data (date): Data da primeira parcela
        Returns:
            list: Lista de parcelas com data e valor
        """
        if not valor_total or not quantidade_parcelas or quantidade_parcelas <= 0:
            return []
        
        parcelas = []
        valor_parcela = Decimal(str(valor_total)) / Decimal(str(quantidade_parcelas))
        valor_parcela = valor_parcela.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Ajustar última parcela para acerto de centavos
        valor_ultima = Decimal(str(valor_total)) - (valor_parcela * (quantidade_parcelas - 1))
        
        for i in range(quantidade_parcelas):
            if i == quantidade_parcelas - 1:
                # Última parcela com ajuste de centavos
                valor = float(valor_ultima)
            else:
                valor = float(valor_parcela)
            
            # Calcular data (se primeira_data fornecida, incrementar mensalmente)
            data = ''
            if primeira_data:
                try:
                    from dateutil.relativedelta import relativedelta
                    data_parcela = primeira_data + relativedelta(months=i)
                    data = data_parcela.strftime('%Y-%m-%d')
                except ImportError:
                    # Se dateutil não disponível, incrementar por 30 dias
                    data_parcela = primeira_data + timedelta(days=30*i)
                    data = data_parcela.strftime('%Y-%m-%d')
            
            parcelas.append({
                'data': data,
                'valor': valor
            })
        
        return parcelas
    
    @staticmethod
    def validar_dados_os(dados):
        """
        Valida os dados da OS antes dos cálculos
        Args:
            dados (dict): Dados da OS
        Returns:
            tuple: (bool, list) - (é_válido, lista_erros)
        """
        erros = []
        
        # Validações obrigatórias
        if not dados.get('cliente_id'):
            erros.append('Cliente é obrigatório')
        
        if not dados.get('data_emissao'):
            erros.append('Data de emissão é obrigatória')
        
        # Validar horas se informadas
        hora_inicio = dados.get('hora_inicio')
        hora_termino = dados.get('hora_termino')
        
        if hora_inicio and hora_termino:
            try:
                datetime.strptime(hora_inicio, '%H:%M')
                datetime.strptime(hora_termino, '%H:%M')
            except ValueError:
                erros.append('Formato de hora inválido (use HH:MM)')
        
        # Validar quilometragem
        km_inicial = dados.get('km_inicial')
        km_final = dados.get('km_final')
        
        if km_inicial and km_final:
            try:
                if float(km_final) < float(km_inicial):
                    erros.append('KM final deve ser maior que KM inicial')
            except (ValueError, TypeError):
                erros.append('Valores de quilometragem inválidos')
        
        return len(erros) == 0, erros
