"""Representação Intermediária Normalizada (NIR) para documentos fiscais eletrônicos.

Permite que as regras fiscais operem sobre estruturas Python tipadas e com precisão
aritmética Decimal, sem acoplamento direto à sintaxe crua do XML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass
class IdentificacaoData:
    """Dados do grupo <ide>."""
    cUF: str
    natOp: str
    mod: str  # 55, 65, 57
    serie: str
    nNF: str
    dhEmi: str
    tpNF: str  # 0=Entrada, 1=Saída
    idDest: str  # 1=Interna, 2=Interestadual, 3=Exterior
    cMunFG: str
    tpImp: str
    tpEmis: str
    finNFe: str  # 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução
    indFinal: str  # 0=Normal, 1=Consumidor Final
    indPres: str
    xml_path: str = "/NFe/infNFe/ide"


@dataclass
class EmitenteData:
    """Dados do grupo <emit>."""
    CNPJ: Optional[str] = None
    CPF: Optional[str] = None
    xNome: str = ""
    xFant: Optional[str] = None
    UF: str = ""
    cMun: Optional[str] = None
    CRT: Optional[str] = None  # 1=Simples Nacional, 2=SN Sublimite, 3=Regime Normal
    xml_path: str = "/NFe/infNFe/emit"


@dataclass
class DestinatarioData:
    """Dados do grupo <dest>."""
    CNPJ: Optional[str] = None
    CPF: Optional[str] = None
    idEstrangeiro: Optional[str] = None
    xNome: str = ""
    UF: str = ""
    cMun: Optional[str] = None
    indIEDest: Optional[str] = None  # 1=Contribuinte, 2=Isento, 9=Não Contribuinte
    xml_path: str = "/NFe/infNFe/dest"


@dataclass
class ICMSData:
    """Dados do grupo <ICMS>."""
    variant: str  # ICMS00, ICMS10, ICMSSN101, etc.
    orig: str
    CST: Optional[str] = None
    CSOSN: Optional[str] = None
    modBC: Optional[str] = None
    vBC: Optional[Decimal] = None
    pICMS: Optional[Decimal] = None
    vICMS: Optional[Decimal] = None
    modBCST: Optional[str] = None
    pMVAST: Optional[Decimal] = None
    pRedBCST: Optional[Decimal] = None
    vBCST: Optional[Decimal] = None
    pICMSST: Optional[Decimal] = None
    vICMSST: Optional[Decimal] = None
    pRedBC: Optional[Decimal] = None
    vICMSDeson: Optional[Decimal] = None
    motDesICMS: Optional[str] = None
    pCredSN: Optional[Decimal] = None
    vCredICMSSN: Optional[Decimal] = None
    vBCSTRet: Optional[Decimal] = None
    vICMSSTRet: Optional[Decimal] = None
    xml_subpath: str = ""


@dataclass
class PISData:
    """Dados do grupo <PIS>."""
    variant: str
    CST: Optional[str] = None
    vBC: Optional[Decimal] = None
    pPIS: Optional[Decimal] = None
    vPIS: Optional[Decimal] = None
    qBCProd: Optional[Decimal] = None
    vAliqProd: Optional[Decimal] = None
    xml_subpath: str = ""


@dataclass
class COFINSData:
    """Dados do grupo <COFINS>."""
    variant: str
    CST: Optional[str] = None
    vBC: Optional[Decimal] = None
    pCOFINS: Optional[Decimal] = None
    vCOFINS: Optional[Decimal] = None
    qBCProd: Optional[Decimal] = None
    vAliqProd: Optional[Decimal] = None
    xml_subpath: str = ""


@dataclass
class IPIData:
    """Dados do grupo <IPI>."""
    CST: Optional[str] = None
    vBC: Optional[Decimal] = None
    pIPI: Optional[Decimal] = None
    vIPI: Optional[Decimal] = None
    xml_subpath: str = ""


@dataclass
class ItemData:
    """Dados do item da nota <det>."""
    nItem: int
    cProd: str
    xProd: str
    NCM: str
    CFOP: str
    uCom: str
    qCom: Decimal
    vUnCom: Decimal
    vProd: Decimal
    cEAN: Optional[str] = None
    CEST: Optional[str] = None
    vFrete: Decimal = Decimal("0.00")
    vSeg: Decimal = Decimal("0.00")
    vDesc: Decimal = Decimal("0.00")
    vOutro: Decimal = Decimal("0.00")
    icms: Optional[ICMSData] = None
    pis: Optional[PISData] = None
    cofins: Optional[COFINSData] = None
    ipi: Optional[IPIData] = None
    xml_path: str = ""


@dataclass
class TotalData:
    """Dados do grupo <total>/<ICMSTot>."""
    vBC: Decimal = Decimal("0.00")
    vICMS: Decimal = Decimal("0.00")
    vICMSDeson: Decimal = Decimal("0.00")
    vFCPUFDest: Decimal = Decimal("0.00")
    vBCST: Decimal = Decimal("0.00")
    vST: Decimal = Decimal("0.00")
    vFCPST: Decimal = Decimal("0.00")
    vFCPSTRet: Decimal = Decimal("0.00")
    vProd: Decimal = Decimal("0.00")
    vFrete: Decimal = Decimal("0.00")
    vSeg: Decimal = Decimal("0.00")
    vDesc: Decimal = Decimal("0.00")
    vII: Decimal = Decimal("0.00")
    vIPI: Decimal = Decimal("0.00")
    vIPIDevol: Decimal = Decimal("0.00")
    vPIS: Decimal = Decimal("0.00")
    vCOFINS: Decimal = Decimal("0.00")
    vOutro: Decimal = Decimal("0.00")
    vNF: Decimal = Decimal("0.00")
    vTotTrib: Decimal = Decimal("0.00")
    xml_path: str = "/NFe/infNFe/total/ICMSTot"


@dataclass
class NormalizedDocument:
    """Representação intermediária padronizada de um DF-e."""
    document_type: str
    layout_version: str
    chave_acesso: Optional[str]
    ide: IdentificacaoData
    emit: EmitenteData
    dest: Optional[DestinatarioData] = None
    itens: List[ItemData] = field(default_factory=list)
    total: Optional[TotalData] = None
    raw_root_prefix: str = "/NFe/infNFe"

