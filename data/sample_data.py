"""Sample data for demonstrating the RAG system capabilities."""

SAMPLE_AUTHORS = [
    "Dr. Sarah Mitchell",
    "Prof. James Rodriguez", 
    "Attorney Lisa Chen"
]

SAMPLE_CONCEPTS = [
    "Constitutional Rights",
    "Privacy Protection", 
    "Data Security",
    "Environmental Law",
    "Corporate Governance"
]

SAMPLE_LAWS = [
    "Section 230",
    "GDPR Article 17",
    "USC Title 42"
]

SAMPLE_DOCUMENTS = [
    {
        "text": """
        The General Data Protection Regulation (GDPR) represents a fundamental shift in how organizations must handle personal data. 
        Under GDPR Article 17, individuals have the right to erasure, commonly known as the "right to be forgotten." This provision 
        requires data controllers to delete personal data under specific circumstances, including when the data is no longer necessary 
        for the original purpose it was collected for.
        
        Organizations must implement technical and organizational measures to ensure compliance with privacy protection requirements. 
        The regulation emphasizes data security as a core principle, requiring companies to demonstrate accountability in their 
        data processing activities. Failure to comply can result in significant penalties, up to 4% of annual global turnover.
        
        The impact on corporate governance has been substantial, as companies must now integrate privacy considerations into their 
        business strategies from the outset. This privacy-by-design approach represents a paradigm shift in how organizations 
        approach data handling and customer rights.
        """,
        "metadata": {
            "source": "GDPR Compliance Guide 2024",
            "author": "Dr. Sarah Mitchell",
            "topic": "privacy_law"
        }
    },
    {
        "text": """
        Constitutional rights in the digital age face unprecedented challenges as technology evolves faster than legal frameworks. 
        The intersection of privacy protection and national security creates complex scenarios that courts must navigate carefully. 
        Recent cases have highlighted the tension between individual privacy rights and collective security interests.
        
        Section 230 of the Communications Decency Act provides immunity to online platforms for user-generated content, but this 
        protection is increasingly scrutinized. Critics argue that this immunity enables the spread of misinformation and harmful 
        content, while supporters contend it protects free speech and innovation online.
        
        The challenge for lawmakers is balancing constitutional protections with the need for responsible platform governance. 
        Environmental law principles suggest that sustainable solutions require comprehensive frameworks that address both 
        immediate concerns and long-term implications for digital rights and freedoms.
        """,
        "metadata": {
            "source": "Digital Rights Quarterly Review",
            "author": "Prof. James Rodriguez", 
            "topic": "constitutional_law"
        }
    },
    {
        "text": """
        Environmental law enforcement has evolved significantly with the integration of data security measures and digital monitoring 
        systems. USC Title 42 establishes the framework for environmental protection, requiring agencies to maintain comprehensive 
        records of compliance activities and enforcement actions.
        
        Modern environmental monitoring relies heavily on data collection systems that must balance transparency with privacy protection. 
        Corporate governance structures in environmental compliance often involve complex relationships between regulatory bodies, 
        private companies, and public interest groups.
        
        The intersection of environmental law and constitutional rights becomes apparent in cases involving public access to 
        environmental data versus corporate proprietary information. Courts must weigh the public's right to know against 
        legitimate business interests in protecting sensitive operational data.
        """,
        "metadata": {
            "source": "Environmental Compliance Manual",
            "author": "Attorney Lisa Chen",
            "topic": "environmental_law"
        }
    },
    {
        "text": """
        Data security in corporate environments requires a multi-layered approach that addresses both technical vulnerabilities 
        and regulatory compliance requirements. Organizations must implement robust security frameworks that protect against 
        both external threats and internal risks to sensitive information.
        
        The principle of privacy protection extends beyond individual rights to encompass corporate responsibilities in 
        safeguarding stakeholder information. This includes employee data, customer information, and proprietary business 
        intelligence that could impact competitive positioning.
        
        Corporate governance frameworks must integrate data security considerations into strategic decision-making processes. 
        Board oversight of cybersecurity risks has become a critical component of effective governance, requiring directors 
        to maintain awareness of emerging threats and regulatory developments in the privacy protection landscape.
        """,
        "metadata": {
            "source": "Corporate Security Best Practices",
            "author": "Dr. Sarah Mitchell",
            "topic": "cybersecurity"
        }
    },
    {
        "text": """
        The evolution of constitutional rights interpretation in digital contexts reflects broader changes in how courts understand 
        technology's impact on fundamental freedoms. Privacy protection has emerged as a central concern in Fourth Amendment 
        jurisprudence, with courts grappling with questions about reasonable expectations of privacy in digital communications.
        
        Recent Supreme Court decisions have established important precedents regarding data security and government surveillance 
        powers. The balance between national security interests and individual privacy rights continues to evolve as new 
        technologies challenge traditional constitutional frameworks.
        
        Environmental law principles offer instructive parallels for digital rights governance, particularly in areas of 
        precautionary regulation and stakeholder participation in policy development. The complexity of modern technological 
        systems requires governance approaches that can adapt to rapid change while maintaining core constitutional protections.
        """,
        "metadata": {
            "source": "Constitutional Law in the Digital Age",
            "author": "Prof. James Rodriguez",
            "topic": "constitutional_law"
        }
    }
]

def get_sample_data():
    """Return structured sample data for the RAG system."""
    return {
        'authors': SAMPLE_AUTHORS,
        'concepts': SAMPLE_CONCEPTS, 
        'laws': SAMPLE_LAWS,
        'documents': SAMPLE_DOCUMENTS
    }