import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral:latest')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './summaries')
    MAX_CHUNK_SIZE = int(os.getenv('MAX_CHUNK_SIZE', 4000))
    
    # Categorization keywords for research studies
    CATEGORIES = {
        'clinical_trial': [
            'clinical trial', 'randomized controlled trial', 'rct', 'phase i', 'phase ii', 'phase iii', 
            'phase iv', 'double blind', 'placebo controlled', 'multicenter', 'intervention', 
            'treatment group', 'control group', 'primary endpoint', 'secondary endpoint', 'efficacy', 
            'safety', 'adverse events', 'participant', 'enrollment', 'clinical study', 'therapeutic'
        ],
        'preclinical_models': [
            'animal model', 'mouse model', 'rat model', 'transgenic', 'knockout', 'in vivo', 
            'preclinical', 'experimental model', 'animal study', 'rodent', 'primate', 'zebrafish', 
            'drosophila', 'c elegans', 'xenograft', 'tumor model', 'disease model', 'behavioral test', 
            'pharmacokinetics', 'toxicity', 'dosing', 'administration'
        ],
        'cellular_studies': [
            'cell culture', 'in vitro', 'cell line', 'primary cells', 'stem cells', 'organoid', 
            'tissue culture', 'cell viability', 'cytotoxicity', 'apoptosis', 'proliferation', 
            'differentiation', 'transfection', 'gene expression', 'protein expression', 'western blot', 
            'flow cytometry', 'microscopy', 'immunofluorescence', 'pcr', 'qpcr', 'rna seq', 
            'crispr', 'sirna', 'overexpression'
        ],
        'meta_analysis': [
            'meta analysis', 'meta-analysis', 'systematic review', 'pooled analysis', 'forest plot', 
            'heterogeneity', 'fixed effects', 'random effects', 'odds ratio', 'risk ratio', 
            'hazard ratio', 'confidence interval', 'cochrane', 'prisma', 'search strategy', 
            'inclusion criteria', 'exclusion criteria', 'bias assessment', 'funnel plot', 
            'publication bias', 'subgroup analysis'
        ],
        'review_article': [
            'review', 'literature review', 'narrative review', 'scoping review', 'overview', 
            'perspective', 'commentary', 'opinion', 'editorial', 'mini review', 'comprehensive review', 
            'state of the art', 'current understanding', 'recent advances', 'future directions', 
            'emerging', 'novel approaches', 'therapeutic targets', 'biomarkers', 'pathophysiology'
        ]
    }