"""Dell-specific document processing service for technical manuals and documentation."""
import re
import uuid
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class DellDocumentProcessor:
    """Service for processing Dell technical documents into chunks suitable for embedding."""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 400):
        """Initialize Dell document processor with chunking parameters optimized for technical content."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Dell-specific patterns based on real manual structure
        self.dell_patterns = {
            'model_numbers': [
                r'\bDell\s+Pro\s+Max\s+\d+\s+Premium\b',  # Dell Pro Max 14 Premium
                r'\bMA\d{5}\b',  # MA14250
                r'\bP\d{3}G\d{3}\b',  # P201G001
                r'\b(?:Latitude|Inspiron|XPS|OptiPlex|Precision|Vostro|PowerEdge|Alienware)\s+[\w\s]+\b'
            ],
            'regulatory_info': [
                r'\bRegulatory\s+Model:\s*([A-Z0-9]+)\b',
                r'\bRegulatory\s+Type:\s*([A-Z0-9]+)\b',
                r'\bService\s+Tag\b',
                r'\bExpress\s+Service\s+Code\b',
                r'\bRev\.\s+([A-Z0-9]+)\b'
            ],
            'specifications': [
                r'\b\d+(?:\.\d+)?\s*(?:GHz|MHz|GB|TB|MB|Wh|V|A|W|TOPS|Gbps)\b',
                r'\b\d+(?:\.\d+)?\s*(?:inch|"|mm|cm|kg|lb)\b',
                r'\b\d+\s*x\s*\d+(?:\s*x\s*\d+)?\b',  # Resolutions like 1920 x 1200
                r'\b(?:Intel|AMD|NVIDIA)\s+[\w\s]+\b',  # Processor/GPU names
                r'\b(?:Core\s+Ultra|Arc\s+Pro|RTX\s+PRO)\s+[\w\s]+\b',
                r'\b\d+\s*(?:dpi|ppi|fps|Hz|MT/s)\b'
            ],
            'safety_warnings': [
                r'\b(?:WARNING|CAUTION|DANGER|NOTICE|IMPORTANT):\s*',
                r'\b(?:Safety|Hazard|Risk|Precaution|ESD)\b'
            ],
            'procedures': [
                r'\b(?:Prerequisites|About\s+this\s+task|Steps|Next\s+steps)\b',
                r'\b(?:Removing|Installing|Replacing)\s+the\s+[\w\s]+\b',
                r'\b(?:Before|After)\s+working\s+inside\s+your\s+computer\b'
            ],
            'components': [
                r'\b(?:System\s+board|Motherboard|Heat\s+sink|Palm\s+rest|Touchpad|Base\s+cover)\b',
                r'\b(?:Battery|Fan|Speaker|Camera|Display|Keyboard|Memory)\b',
                r'\b(?:Thunderbolt|USB|HDMI|Audio|Power)\s+(?:port|connector|cable)\b',
                r'\b(?:M\.2|SSD|HDD|Storage|Drive)\b',
                r'\b(?:Left|Right|Front|Back|Top|Bottom)\s+(?:I/O-board|hinge|fan|speaker)\b',
                r'\b(?:Customer\s+Replaceable\s+Units?|CRUs?)\b',
                r'\b(?:Field\s+Replaceable\s+Units?|FRUs?)\b'
            ],
            'ports_connectors': [
                r'\bThunderbolt\s+\d+\s*\([^)]+\)\b',
                r'\bmicroSD\s+card\s+slot\b',
                r'\bGlobal\s+headset\s+port\b',
                r'\bSecurity-cable\s+slot\b',
                r'\bUSB\s+Type-C\b',
                r'\bDisplayPort\s+\d+\.\d+\b'
            ],
            'technical_terms': [
                r'\b(?:BIOS|UEFI|TPM|BitLocker|ExpressCharge)\b',
                r'\b(?:Service\s+Mode|ESD\s+protection)\b',
                r'\b(?:LPDDR5x|GDDR7|NVMe|PCIe)\b',
                r'\b(?:Wi-Fi\s+\d+|Bluetooth\s+\d+\.\d+)\b'
            ],
            'chapter_sections': [
                r'\bChapter\s+\d+:\s*[^\n]+\b',
                r'\bTable\s+\d+\.\s*[^\n]+\b',
                r'\bFigure\s+\d+\.\s*[^\n]+\b'
            ]
        }
    
    def split_text(self, text: str) -> List[str]:
        """Split Dell technical text into overlapping chunks with section awareness."""
        # Clean the text
        text = self._clean_technical_text(text)
        
        # Split by sections first (Dell manuals have clear chapter/section structure)
        sections = self._split_into_sections(text)
        
        chunks = []
        
        for section in sections:
            # If section is small enough, keep as single chunk
            if len(section) <= self.chunk_size:
                if section.strip():
                    chunks.append(section.strip())
                continue
            
            # Split large sections into smaller chunks
            section_chunks = self._split_section_into_chunks(section)
            chunks.extend(section_chunks)
        
        logger.info(f"Split Dell document into {len(chunks)} chunks")
        return chunks
    
    def _clean_technical_text(self, text: str) -> str:
        """Clean technical text while preserving important formatting and technical terms."""
        # Remove excessive whitespace but preserve line breaks for procedures
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Preserve technical formatting and special characters
        text = re.sub(r'([A-Z]{2,})\s+([A-Z]{2,})', r'\1 \2', text)  # Keep acronyms spaced properly
        
        # Clean up common OCR artifacts while preserving technical symbols
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\n\r\/\\@#\$%\^&\*\+=<>°]', ' ', text)
        
        return text.strip()
    
    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into logical sections based on Dell manual structure."""
        # Dell manual section patterns based on actual structure
        section_patterns = [
            r'\nChapter\s+\d+:\s*[^\n]+\n',  # Chapter 1: Views of Dell Pro Max
            r'\n[A-Z][a-z][^\n]{15,}\n(?=\n|[A-Z])',  # Section headers like "Dimensions and weight"
            r'\n(?:Table\s+\d+\.|Figure\s+\d+\.)\s*[^\n]+\n',  # Tables and figures
            r'\n(?:WARNING|CAUTION|NOTICE|IMPORTANT|NOTE):\s*',  # Safety/info notices
            r'\n(?:Prerequisites|About\s+this\s+task|Steps|Next\s+steps)\n',  # Procedure sections
            r'\n(?:Removing|Installing)\s+[^\n]+\n',  # Procedure titles
            r'\n\d+\.\s+[A-Z][^\n]+\n',  # Numbered items
            r'\n[A-Z][A-Z\s]{10,}\n'  # ALL CAPS HEADERS
        ]
        
        # Find section breaks
        section_breaks = [0]
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                section_breaks.append(match.start())
        
        # Remove duplicates and sort
        section_breaks = sorted(list(set(section_breaks)))
        section_breaks.append(len(text))
        
        # Create sections
        sections = []
        for i in range(len(section_breaks) - 1):
            section = text[section_breaks[i]:section_breaks[i + 1]].strip()
            if section and len(section) > 50:  # Filter out very short sections
                sections.append(section)
        
        return sections if sections else [text]
    
    def _split_section_into_chunks(self, section: str) -> List[str]:
        """Split a large section into smaller chunks with overlap."""
        # Split by sentences/procedures for technical content
        units = self._split_into_technical_units(section)
        
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for unit in units:
            unit_length = len(unit)
            
            # If adding this unit would exceed chunk size, finalize current chunk
            if current_length + unit_length > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + unit
                current_length = len(current_chunk)
            else:
                current_chunk += " " + unit if current_chunk else unit
                current_length += unit_length
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_technical_units(self, text: str) -> List[str]:
        """Split text into technical units (sentences, steps, bullet points)."""
        # Split on various technical document delimiters
        units = re.split(r'[.!?]+\s+|\n\s*[-•]\s+|\n\s*\d+\.\s+|\n\s*[a-z]\)\s+|\n\s*Steps?\s*\n', text)
        
        # Filter out empty units and strip whitespace
        units = [unit.strip() for unit in units if unit.strip() and len(unit.strip()) > 10]
        return units
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get the last `overlap_size` characters as overlap text, preferring sentence boundaries."""
        if len(text) <= overlap_size:
            return text
        
        # Try to find a sentence boundary within the overlap region
        overlap_text = text[-overlap_size:]
        sentence_end = overlap_text.rfind('.')
        
        if sentence_end > overlap_size // 2:  # If we find a sentence end in the latter half
            return text[-(overlap_size - sentence_end - 1):]
        
        return overlap_text
    
    def create_document_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Dell document chunks with metadata and UUIDs."""
        chunks = self.split_text(text)
        document_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Extract Dell-specific entities from this chunk
            chunk_entities = self.extract_dell_entities(chunk)
            
            # Determine chunk type based on content
            chunk_type = self._determine_chunk_type(chunk)
            
            chunk_data = {
                'id': str(uuid.uuid4()),
                'text': chunk,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_type': chunk_type,
                'entities': chunk_entities,
                'document_type': 'dell_technical_manual',
                **metadata  # Include all provided metadata
            }
            document_chunks.append(chunk_data)
        
        return document_chunks
    
    def _determine_chunk_type(self, chunk: str) -> str:
        """Determine the type of content in a chunk."""
        chunk_lower = chunk.lower()
        
        if re.search(r'\bchapter\s+\d+:', chunk_lower):
            return 'chapter_header'
        elif re.search(r'\b(?:table|figure)\s+\d+\.', chunk_lower):
            return 'table_figure'
        elif re.search(r'\b(?:warning|caution|danger):', chunk_lower):
            return 'safety_warning'
        elif re.search(r'\b(?:prerequisites|steps|next\s+steps)', chunk_lower):
            return 'procedure'
        elif re.search(r'\b(?:removing|installing)\s+the\s+', chunk_lower):
            return 'installation_procedure'
        elif re.search(r'\b\d+(?:\.\d+)?\s*(?:ghz|mhz|gb|tb|mb|wh|v|a|w)\b', chunk_lower):
            return 'specifications'
        elif re.search(r'\b(?:dimensions|weight|processor|memory|display)\b', chunk_lower):
            return 'technical_specs'
        else:
            return 'general_content'
    
    def extract_dell_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Dell-specific entities from text."""
        entities = {
            'model_numbers': [],
            'regulatory_info': [],
            'specifications': [],
            'safety_warnings': [],
            'procedures': [],
            'components': [],
            'ports_connectors': [],
            'technical_terms': [],
            'chapter_sections': []
        }
        
        # Extract entities using Dell-specific patterns
        for entity_type, patterns in self.dell_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Clean and deduplicate matches
                    if isinstance(matches[0], tuple):
                        # Handle regex groups
                        clean_matches = [match[0] if isinstance(match, tuple) else match for match in matches]
                    else:
                        clean_matches = matches
                    
                    clean_matches = [match.strip() for match in clean_matches if match.strip()]
                    entities[entity_type].extend(clean_matches)
            
            # Remove duplicates while preserving order
            entities[entity_type] = list(dict.fromkeys(entities[entity_type]))
        
        return entities
    
    def extract_technical_metadata(self, text: str) -> Dict[str, Any]:
        """Extract technical metadata specific to Dell documents."""
        metadata = {}
        
        # Extract document title and model from header
        header_text = text[:2000]
        
        # Dell Pro Max 14 Premium pattern
        title_match = re.search(r'Dell\s+Pro\s+Max\s+\d+\s+Premium', header_text, re.IGNORECASE)
        if title_match:
            metadata['document_title'] = title_match.group().strip()
        
        # Model number (MA14250)
        model_match = re.search(r'\b(MA\d{5})\b', header_text)
        if model_match:
            metadata['model_number'] = model_match.group(1)
        
        # Document type
        doc_type_match = re.search(r"Owner's\s+Manual|Service\s+Manual|Setup\s+Guide", header_text, re.IGNORECASE)
        if doc_type_match:
            metadata['document_type'] = doc_type_match.group().strip()
        
        # Regulatory information
        regulatory_info = {}
        reg_model_match = re.search(r'Regulatory\s+Model:\s*([A-Z0-9]+)', text)
        if reg_model_match:
            regulatory_info['regulatory_model'] = reg_model_match.group(1)
        
        reg_type_match = re.search(r'Regulatory\s+Type:\s*([A-Z0-9]+)', text)
        if reg_type_match:
            regulatory_info['regulatory_type'] = reg_type_match.group(1)
        
        if regulatory_info:
            metadata['regulatory'] = regulatory_info
        
        # Extract revision information
        revision_match = re.search(r'Rev\.\s+([A-Z0-9]+)', text)
        if revision_match:
            metadata['revision'] = revision_match.group(1)
        
        # Extract publication date
        date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', text)
        if date_match:
            metadata['publication_date'] = date_match.group()
        
        # Count different types of content with more accurate patterns
        content_stats = {
            'chapters': len(re.findall(r'Chapter\s+\d+:', text)),
            'safety_warnings': len(re.findall(r'\b(?:WARNING|CAUTION|DANGER):', text)),
            'procedures': len(re.findall(r'\b(?:Removing|Installing)\s+the\s+', text, re.IGNORECASE)),
            'specifications': len(re.findall(r'\b\d+(?:\.\d+)?\s*(?:GHz|MHz|GB|TB|MB|Wh|V|A|W|TOPS|Gbps)\b', text)),
            'tables': len(re.findall(r'Table\s+\d+\.', text)),
            'figures': len(re.findall(r'Figure\s+\d+\.', text)),
            'ports': len(re.findall(r'\b(?:Thunderbolt|USB|HDMI|Audio)\s+port', text, re.IGNORECASE)),
            'components': len(re.findall(r'\b(?:System\s+board|Heat\s+sink|Battery|Fan|Display)\b', text, re.IGNORECASE))
        }
        metadata['content_stats'] = content_stats
        
        # Extract key specifications if found
        specs = {}
        
        # Processor information
        proc_match = re.search(r'Intel\s+Core\s+Ultra\s+\d+\s+\w+', text)
        if proc_match:
            specs['processor'] = proc_match.group()
        
        # Memory information
        memory_match = re.search(r'(\d+)\s+GB.*LPDDR5x', text)
        if memory_match:
            specs['memory'] = f"{memory_match.group(1)} GB LPDDR5x"
        
        # Display information
        display_match = re.search(r'(\d+)\s*x\s*(\d+)', text)
        if display_match:
            specs['display_resolution'] = f"{display_match.group(1)}x{display_match.group(2)}"
        
        # Battery information
        battery_match = re.search(r'(\d+)\s*Wh', text)
        if battery_match:
            specs['battery'] = f"{battery_match.group(1)} Wh"
        
        if specs:
            metadata['key_specifications'] = specs
        
        return metadata
    
    def process_dell_document(self, extracted_text: str, source_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a complete Dell document and return structured data."""
        if source_metadata is None:
            source_metadata = {}
        
        # Extract technical metadata
        tech_metadata = self.extract_technical_metadata(extracted_text)
        
        # Combine metadata
        combined_metadata = {
            'source': 'dell_technical_document',
            'processor': 'dell_document_processor_v2',
            'processing_timestamp': None,  # Will be set by the system
            **source_metadata,
            **tech_metadata
        }
        
        # Create document chunks
        chunks = self.create_document_chunks(extracted_text, combined_metadata)
        
        # Extract overall document entities
        document_entities = self.extract_dell_entities(extracted_text)
        
        # Analyze chunk types
        chunk_type_distribution = {}
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            chunk_type_distribution[chunk_type] = chunk_type_distribution.get(chunk_type, 0) + 1
        
        return {
            'chunks': chunks,
            'metadata': combined_metadata,
            'entities': document_entities,
            'chunk_count': len(chunks),
            'total_length': len(extracted_text),
            'chunk_type_distribution': chunk_type_distribution,
            'processing_summary': {
                'avg_chunk_size': sum(len(chunk['text']) for chunk in chunks) // len(chunks) if chunks else 0,
                'entity_types_found': len([k for k, v in document_entities.items() if v]),
                'total_entities': sum(len(v) for v in document_entities.values())
            }
        }
