"""Parser para documentos eletrônicos NF-e (mod 55) e NFC-e (mod 65).

Converte a árvore XML em NormalizedDocument rastreando caminhos XPath precisos.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional
import xml.etree.ElementTree as ET

from ..ingestion import DocumentIngestion
from ..normalization.models import (
    COFINSData,
    DestinatarioData,
    EmitenteData,
    ICMSData,
    IdentificacaoData,
    IPIData,
    ItemData,
    NormalizedDocument,
    PISData,
    TotalData,
)


def _to_decimal(val: Optional[str], default: Decimal = Decimal("0.00")) -> Decimal:
    if not val or not val.strip():
        return default
    try:
        clean = val.strip().replace(",", ".")
        return Decimal(clean)
    except InvalidOperation:
        return default


def _find_child(elem: ET.Element, tag_name: str) -> Optional[ET.Element]:
    for child in elem:
        if DocumentIngestion.extract_clean_tag(child.tag) == tag_name:
            return child
    return None


def _get_text(elem: Optional[ET.Element], tag_name: str, default: str = "") -> str:
    if elem is None:
        return default
    child = _find_child(elem, tag_name)
    if child is not None and child.text is not None:
        return child.text.strip()
    return default


class NFeParser:
    """Extrai entidades fiscais e cria NormalizedDocument com caminhos precisos."""

    @classmethod
    def parse(cls, root: ET.Element, doc_type: str = "NFE", layout_version: Optional[str] = None) -> NormalizedDocument:
        root_tag = DocumentIngestion.extract_clean_tag(root.tag)
        is_proc = root_tag == "nfeProc"

        # Localiza infNFe
        inf_nfe = None
        if is_proc:
            nfe_elem = _find_child(root, "NFe")
            if nfe_elem is not None:
                inf_nfe = _find_child(nfe_elem, "infNFe")
                root_prefix = "/nfeProc/NFe/infNFe"
            else:
                inf_nfe = _find_child(root, "infNFe")
                root_prefix = "/nfeProc/infNFe"
        else:
            if root_tag == "NFe":
                inf_nfe = _find_child(root, "infNFe")
                root_prefix = "/NFe/infNFe"
            elif root_tag == "infNFe":
                inf_nfe = root
                root_prefix = "/infNFe"
            else:
                # Fallback de busca iterativa
                for elem in root.iter():
                    if DocumentIngestion.extract_clean_tag(elem.tag) == "infNFe":
                        inf_nfe = elem
                        break
                root_prefix = f"/{root_tag}/infNFe"

        if inf_nfe is None:
            raise ValueError("Elemento <infNFe> não encontrado no XML.")

        ver = layout_version or inf_nfe.attrib.get("versao", "4.00")
        raw_id = inf_nfe.attrib.get("Id", "")
        access_key = raw_id[3:] if raw_id.startswith("NFe") else (raw_id if len(raw_id) == 44 else None)

        # 1. ide
        ide_elem = _find_child(inf_nfe, "ide")
        ide = IdentificacaoData(
            cUF=_get_text(ide_elem, "cUF"),
            natOp=_get_text(ide_elem, "natOp"),
            mod=_get_text(ide_elem, "mod", "55"),
            serie=_get_text(ide_elem, "serie", "1"),
            nNF=_get_text(ide_elem, "nNF", "1"),
            dhEmi=_get_text(ide_elem, "dhEmi"),
            tpNF=_get_text(ide_elem, "tpNF", "1"),
            idDest=_get_text(ide_elem, "idDest", "1"),
            cMunFG=_get_text(ide_elem, "cMunFG"),
            tpImp=_get_text(ide_elem, "tpImp", "1"),
            tpEmis=_get_text(ide_elem, "tpEmis", "1"),
            finNFe=_get_text(ide_elem, "finNFe", "1"),
            indFinal=_get_text(ide_elem, "indFinal", "0"),
            indPres=_get_text(ide_elem, "indPres", "1"),
            xml_path=f"{root_prefix}/ide",
        )

        # 2. emit
        emit_elem = _find_child(inf_nfe, "emit")
        emit_ender = _find_child(emit_elem, "enderEmit") if emit_elem is not None else None
        emit = EmitenteData(
            CNPJ=_get_text(emit_elem, "CNPJ") or None,
            CPF=_get_text(emit_elem, "CPF") or None,
            xNome=_get_text(emit_elem, "xNome"),
            xFant=_get_text(emit_elem, "xFant") or None,
            UF=_get_text(emit_ender, "UF"),
            cMun=_get_text(emit_ender, "cMun") or None,
            CRT=_get_text(emit_elem, "CRT") or None,
            xml_path=f"{root_prefix}/emit",
        )

        # 3. dest
        dest_elem = _find_child(inf_nfe, "dest")
        dest = None
        if dest_elem is not None:
            dest_ender = _find_child(dest_elem, "enderDest")
            dest = DestinatarioData(
                CNPJ=_get_text(dest_elem, "CNPJ") or None,
                CPF=_get_text(dest_elem, "CPF") or None,
                idEstrangeiro=_get_text(dest_elem, "idEstrangeiro") or None,
                xNome=_get_text(dest_elem, "xNome"),
                UF=_get_text(dest_ender, "UF"),
                cMun=_get_text(dest_ender, "cMun") or None,
                indIEDest=_get_text(dest_elem, "indIEDest") or None,
                xml_path=f"{root_prefix}/dest",
            )

        # 4. det (itens)
        itens = []
        det_idx = 1
        for child in inf_nfe:
            if DocumentIngestion.extract_clean_tag(child.tag) != "det":
                continue

            det_path = f"{root_prefix}/det[{det_idx}]"
            n_item_str = child.attrib.get("nItem", str(det_idx))
            try:
                n_item = int(n_item_str)
            except ValueError:
                n_item = det_idx

            prod_elem = _find_child(child, "prod")
            imposto_elem = _find_child(child, "imposto")

            # Produto
            c_prod = _get_text(prod_elem, "cProd")
            c_ean = _get_text(prod_elem, "cEAN") or None
            x_prod = _get_text(prod_elem, "xProd")
            ncm = _get_text(prod_elem, "NCM")
            cest = _get_text(prod_elem, "CEST") or None
            cfop = _get_text(prod_elem, "CFOP")
            u_com = _get_text(prod_elem, "uCom")
            q_com = _to_decimal(_get_text(prod_elem, "qCom"))
            v_un_com = _to_decimal(_get_text(prod_elem, "vUnCom"))
            v_prod = _to_decimal(_get_text(prod_elem, "vProd"))
            v_frete = _to_decimal(_get_text(prod_elem, "vFrete"))
            v_seg = _to_decimal(_get_text(prod_elem, "vSeg"))
            v_desc = _to_decimal(_get_text(prod_elem, "vDesc"))
            v_outro = _to_decimal(_get_text(prod_elem, "vOutro"))

            # ICMS
            icms_data = None
            if imposto_elem is not None:
                icms_group = _find_child(imposto_elem, "ICMS")
                if icms_group is not None and len(icms_group) > 0:
                    spec_icms = icms_group[0]
                    var_name = DocumentIngestion.extract_clean_tag(spec_icms.tag)
                    subpath = f"{det_path}/imposto/ICMS/{var_name}"

                    v_bc_str = _get_text(spec_icms, "vBC")
                    p_icms_str = _get_text(spec_icms, "pICMS")
                    v_icms_str = _get_text(spec_icms, "vICMS")
                    v_bc_st_str = _get_text(spec_icms, "vBCST")
                    p_icms_st_str = _get_text(spec_icms, "pICMSST")
                    v_icms_st_str = _get_text(spec_icms, "vICMSST")
                    v_deson_str = _get_text(spec_icms, "vICMSDeson")

                    icms_data = ICMSData(
                        variant=var_name,
                        orig=_get_text(spec_icms, "orig", "0"),
                        CST=_get_text(spec_icms, "CST") or None,
                        CSOSN=_get_text(spec_icms, "CSOSN") or None,
                        modBC=_get_text(spec_icms, "modBC") or None,
                        vBC=_to_decimal(v_bc_str) if v_bc_str else None,
                        pICMS=_to_decimal(p_icms_str) if p_icms_str else None,
                        vICMS=_to_decimal(v_icms_str) if v_icms_str else None,
                        modBCST=_get_text(spec_icms, "modBCST") or None,
                        pMVAST=_to_decimal(_get_text(spec_icms, "pMVAST")) if _get_text(spec_icms, "pMVAST") else None,
                        pRedBCST=_to_decimal(_get_text(spec_icms, "pRedBCST")) if _get_text(spec_icms, "pRedBCST") else None,
                        vBCST=_to_decimal(v_bc_st_str) if v_bc_st_str else None,
                        pICMSST=_to_decimal(p_icms_st_str) if p_icms_st_str else None,
                        vICMSST=_to_decimal(v_icms_st_str) if v_icms_st_str else None,
                        pRedBC=_to_decimal(_get_text(spec_icms, "pRedBC")) if _get_text(spec_icms, "pRedBC") else None,
                        vICMSDeson=_to_decimal(v_deson_str) if v_deson_str else None,
                        motDesICMS=_get_text(spec_icms, "motDesICMS") or None,
                        pCredSN=_to_decimal(_get_text(spec_icms, "pCredSN")) if _get_text(spec_icms, "pCredSN") else None,
                        vCredICMSSN=_to_decimal(_get_text(spec_icms, "vCredICMSSN")) if _get_text(spec_icms, "vCredICMSSN") else None,
                        vBCSTRet=_to_decimal(_get_text(spec_icms, "vBCSTRet")) if _get_text(spec_icms, "vBCSTRet") else None,
                        vICMSSTRet=_to_decimal(_get_text(spec_icms, "vICMSSTRet")) if _get_text(spec_icms, "vICMSSTRet") else None,
                        xml_subpath=subpath,
                    )

            # PIS
            pis_data = None
            if imposto_elem is not None:
                pis_group = _find_child(imposto_elem, "PIS")
                if pis_group is not None and len(pis_group) > 0:
                    spec_pis = pis_group[0]
                    pvar = DocumentIngestion.extract_clean_tag(spec_pis.tag)
                    subpath = f"{det_path}/imposto/PIS/{pvar}"
                    v_bc_p = _get_text(spec_pis, "vBC")
                    p_pis = _get_text(spec_pis, "pPIS")
                    v_pis = _get_text(spec_pis, "vPIS")
                    pis_data = PISData(
                        variant=pvar,
                        CST=_get_text(spec_pis, "CST") or None,
                        vBC=_to_decimal(v_bc_p) if v_bc_p else None,
                        pPIS=_to_decimal(p_pis) if p_pis else None,
                        vPIS=_to_decimal(v_pis) if v_pis else None,
                        xml_subpath=subpath,
                    )

            # COFINS
            cofins_data = None
            if imposto_elem is not None:
                cofins_group = _find_child(imposto_elem, "COFINS")
                if cofins_group is not None and len(cofins_group) > 0:
                    spec_cofins = cofins_group[0]
                    cvar = DocumentIngestion.extract_clean_tag(spec_cofins.tag)
                    subpath = f"{det_path}/imposto/COFINS/{cvar}"
                    v_bc_c = _get_text(spec_cofins, "vBC")
                    p_cof = _get_text(spec_cofins, "pCOFINS")
                    v_cof = _get_text(spec_cofins, "vCOFINS")
                    cofins_data = COFINSData(
                        variant=cvar,
                        CST=_get_text(spec_cofins, "CST") or None,
                        vBC=_to_decimal(v_bc_c) if v_bc_c else None,
                        pCOFINS=_to_decimal(p_cof) if p_cof else None,
                        vCOFINS=_to_decimal(v_cof) if v_cof else None,
                        xml_subpath=subpath,
                    )

            # IPI
            ipi_data = None
            if imposto_elem is not None:
                ipi_group = _find_child(imposto_elem, "IPI")
                if ipi_group is not None:
                    ipi_trib = _find_child(ipi_group, "IPITrib") or _find_child(ipi_group, "IPINT")
                    if ipi_trib is not None:
                        subpath = f"{det_path}/imposto/IPI/{DocumentIngestion.extract_clean_tag(ipi_trib.tag)}"
                        v_bc_i = _get_text(ipi_trib, "vBC")
                        p_ipi = _get_text(ipi_trib, "pIPI")
                        v_ipi = _get_text(ipi_trib, "vIPI")
                        ipi_data = IPIData(
                            CST=_get_text(ipi_trib, "CST") or None,
                            vBC=_to_decimal(v_bc_i) if v_bc_i else None,
                            pIPI=_to_decimal(p_ipi) if p_ipi else None,
                            vIPI=_to_decimal(v_ipi) if v_ipi else None,
                            xml_subpath=subpath,
                        )

            item = ItemData(
                nItem=n_item,
                cProd=c_prod,
                xProd=x_prod,
                NCM=ncm,
                CFOP=cfop,
                uCom=u_com,
                qCom=q_com,
                vUnCom=v_un_com,
                vProd=v_prod,
                cEAN=c_ean,
                CEST=cest,
                vFrete=v_frete,
                vSeg=v_seg,
                vDesc=v_desc,
                vOutro=v_outro,
                icms=icms_data,
                pis=pis_data,
                cofins=cofins_data,
                ipi=ipi_data,
                xml_path=det_path,
            )
            itens.append(item)
            det_idx += 1

        # 5. total / ICMSTot
        total = None
        tot_elem = _find_child(inf_nfe, "total")
        if tot_elem is not None:
            icms_tot = _find_child(tot_elem, "ICMSTot")
            if icms_tot is not None:
                total = TotalData(
                    vBC=_to_decimal(_get_text(icms_tot, "vBC")),
                    vICMS=_to_decimal(_get_text(icms_tot, "vICMS")),
                    vICMSDeson=_to_decimal(_get_text(icms_tot, "vICMSDeson")),
                    vFCPUFDest=_to_decimal(_get_text(icms_tot, "vFCPUFDest")),
                    vBCST=_to_decimal(_get_text(icms_tot, "vBCST")),
                    vST=_to_decimal(_get_text(icms_tot, "vST")),
                    vFCPST=_to_decimal(_get_text(icms_tot, "vFCPST")),
                    vFCPSTRet=_to_decimal(_get_text(icms_tot, "vFCPSTRet")),
                    vProd=_to_decimal(_get_text(icms_tot, "vProd")),
                    vFrete=_to_decimal(_get_text(icms_tot, "vFrete")),
                    vSeg=_to_decimal(_get_text(icms_tot, "vSeg")),
                    vDesc=_to_decimal(_get_text(icms_tot, "vDesc")),
                    vII=_to_decimal(_get_text(icms_tot, "vII")),
                    vIPI=_to_decimal(_get_text(icms_tot, "vIPI")),
                    vIPIDevol=_to_decimal(_get_text(icms_tot, "vIPIDevol")),
                    vPIS=_to_decimal(_get_text(icms_tot, "vPIS")),
                    vCOFINS=_to_decimal(_get_text(icms_tot, "vCOFINS")),
                    vOutro=_to_decimal(_get_text(icms_tot, "vOutro")),
                    vNF=_to_decimal(_get_text(icms_tot, "vNF")),
                    vTotTrib=_to_decimal(_get_text(icms_tot, "vTotTrib")),
                    xml_path=f"{root_prefix}/total/ICMSTot",
                )

        return NormalizedDocument(
            document_type=doc_type,
            layout_version=ver,
            chave_acesso=access_key,
            ide=ide,
            emit=emit,
            dest=dest,
            itens=itens,
            total=total,
            raw_root_prefix=root_prefix,
        )

