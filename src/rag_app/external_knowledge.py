# src/rag_app/external_knowledge.py
"""
Sistema de Conhecimento Externo para RAG
Permite buscar informações complementares quando os documentos locais são insuficientes.
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from .config import EXTERNAL_KNOWLEDGE_CONFIG

logger = logging.getLogger(__name__)

class ExternalKnowledgeProvider:
    """Provedor de conhecimento externo para complementar informações dos documentos locais."""
    
    def __init__(self):
        self.config = EXTERNAL_KNOWLEDGE_CONFIG
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-System/1.0 (Educational Research)'
        })
    
    def should_use_external_knowledge(self, query: str, local_chunks: List[Dict], 
                                    confidence_scores: List[float]) -> bool:
        """
        Determina se deve usar conhecimento externo baseado na qualidade dos chunks locais.
        
        Args:
            query: Pergunta do usuário
            local_chunks: Chunks encontrados nos documentos locais
            confidence_scores: Scores de confiança dos chunks
            
        Returns:
            True se deve buscar conhecimento externo, False caso contrário
        """
        # Verificar se há palavras-chave que impedem uso externo
        query_lower = query.lower()
        for keyword in self.config["specific_context_keywords"]:
            if keyword in query_lower:
                logger.info(f"Uso externo bloqueado por palavra-chave específica: {keyword}")
                return False
        
        # Verificar se há chunks suficientes e com boa qualidade
        if len(local_chunks) >= self.config["min_chunks_threshold"]:
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            if avg_confidence >= self.config["confidence_threshold"]:
                logger.info(f"Chunks locais suficientes (conf: {avg_confidence:.2f})")
                return False
        
        # Verificar se é pergunta conceitual
        for keyword in self.config["conceptual_keywords"]:
            if keyword in query_lower:
                logger.info(f"Pergunta conceitual detectada: {keyword}")
                return True
                
        # Se poucos chunks ou baixa confiança, considerar uso externo
        if len(local_chunks) < self.config["min_chunks_threshold"]:
            logger.info(f"Poucos chunks locais ({len(local_chunks)}), considerando fonte externa")
            return True
            
        return False
    
    def search_wikipedia(self, query: str, language: str = "pt") -> Optional[Dict]:
        """
        Busca informações na Wikipedia.
        
        Args:
            query: Termo a ser pesquisado
            language: Idioma da Wikipedia (pt, en)
            
        Returns:
            Dicionário com título, resumo e URL ou None se não encontrar
        """
        try:
            # API da Wikipedia para busca
            search_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{query}"
            
            response = self.session.get(search_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if 'extract' in data and len(data['extract']) > 50:
                    return {
                        'title': data.get('title', ''),
                        'summary': data.get('extract', ''),
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'source': 'Wikipedia'
                    }
            
        except Exception as e:
            logger.error(f"Erro ao buscar na Wikipedia: {e}")
            
        return None
    
    def search_educational_concepts(self, query: str) -> Optional[Dict]:
        """
        Busca conceitos educacionais básicos.
        
        Args:
            query: Termo educacional a ser pesquisado
            
        Returns:
            Dicionário com informação conceitual ou None
        """
        # Base de conhecimento educacional básico
        educational_concepts = {
            "renda per capita": {
                'definition': 'Renda per capita é o valor da renda total de uma família ou grupo dividido pelo número de pessoas. É calculada somando-se todas as rendas e dividindo pelo número de membros.',
                'calculation': 'Fórmula: Renda Per Capita = Soma de todas as rendas ÷ Número de pessoas',
                'example': 'Se uma família tem renda total de R$ 3.000 e 4 membros, a renda per capita é R$ 750.',
                'source': 'Conceito Econômico Básico'
            },
            "renda bruta": {
                'definition': 'Renda bruta é o valor total recebido antes de descontos de impostos, contribuições ou outras deduções.',
                'difference': 'Diferente da renda líquida, que é o valor após os descontos.',
                'components': 'Inclui salários, pensões, aluguéis, rendimentos de aplicações, etc.',
                'source': 'Conceito Econômico Básico'
            },
            "salário mínimo": {
                'definition': 'Salário mínimo é o menor valor de remuneração que um empregador pode pagar legalmente a um trabalhador.',
                'purpose': 'Estabelece um piso salarial para garantir condições mínimas de subsistência.',
                'variation': 'O valor pode variar por região ou ser nacional, conforme legislação local.',
                'source': 'Conceito Trabalhista'
            },
            "cotas": {
                'definition': 'Sistema de cotas é uma política de ação afirmativa que reserva vagas para grupos específicos.',
                'purpose': 'Busca promover inclusão e reduzir desigualdades no acesso a oportunidades.',
                'types': 'Podem ser por renda, raça, deficiência, escola pública, etc.',
                'source': 'Conceito de Política Pública'
            }
        }
        
        query_lower = query.lower()
        for concept, info in educational_concepts.items():
            if concept in query_lower:
                return {
                    'concept': concept,
                    'information': info,
                    'source': 'Base de Conhecimento Educacional'
                }
        
        return None
    
    def get_external_knowledge(self, query: str) -> Optional[str]:
        """
        Busca conhecimento externo para complementar a resposta.
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            Texto com conhecimento externo formatado ou None
        """
        # Tentar conceitos educacionais primeiro
        educational_info = self.search_educational_concepts(query)
        if educational_info:
            info = educational_info['information']
            result = f"💡 **Contexto geral sobre {educational_info['concept']}:**\n"
            result += f"- {info['definition']}\n"
            
            if 'calculation' in info:
                result += f"- {info['calculation']}\n"
            if 'example' in info:
                result += f"- {info['example']}\n"
                
            result += f"\n*Fonte: {info['source']}*"
            return result
        
        # Tentar Wikipedia como fallback
        # Extrair termos principais da query
        key_terms = []
        for word in query.split():
            if len(word) > 3 and word.lower() not in ['como', 'para', 'qual', 'onde', 'quando']:
                key_terms.append(word)
        
        for term in key_terms[:2]:  # Tentar os 2 primeiros termos
            wiki_info = self.search_wikipedia(term)
            if wiki_info and len(wiki_info['summary']) > 100:
                return f"💡 **Contexto geral ({wiki_info['title']}):**\n{wiki_info['summary'][:300]}...\n\n*Fonte: {wiki_info['source']} - {wiki_info['url']}*"
        
        return None
    
    def format_response_with_external(self, local_response: str, external_info: str, 
                                    query: str) -> str:
        """
        Formata resposta combinando informações locais e externas.
        
        Args:
            local_response: Resposta baseada nos documentos locais
            external_info: Informação externa complementar
            query: Pergunta original
            
        Returns:
            Resposta formatada combinando ambas as fontes
        """
        if self.config["show_external_indicator"]:
            response = f"{local_response}\n\n{self.config['external_indicator_template']}\n\n{external_info}"
        else:
            response = f"{local_response}\n\n{external_info}"
        
        # Adicionar disclaimer
        response += f"\n\n{self.config['external_disclaimer']}"
        
        if self.config["log_external_usage"]:
            logger.info(f"Conhecimento externo usado para query: '{query[:50]}...'")
        
        return response