from __future__ import annotations

import re
import unicodedata

EXPECTED_CORE = {
    "competenciamov",
    "uf",
    "municipio",
    "saldomovimentacao",
    "cbo2002ocupacao",
    "tipomovimentacao",
    "salario",
}

COLUMN_RENAME = {
    "competenciamov": "competencia_mov",
    "regiao": "regiao_codigo",
    "uf": "uf_codigo",
    "municipio": "municipio_codigo_caged",
    "secao": "cnae_secao",
    "subclasse": "cnae_subclasse",
    "saldomovimentacao": "saldo_movimentacao",
    "categoria": "categoria",
    "cbo2002ocupacao": "cbo_codigo",
    "graudeinstrucao": "grau_instrucao",
    "idade": "idade",
    "horascontratuais": "horas_contratuais",
    "racacor": "raca_cor",
    "sexo": "sexo",
    "tipoempregador": "tipo_empregador",
    "tipoestabelecimento": "tipo_estabelecimento",
    "tipomovimentacao": "tipo_movimentacao",
    "tipodedeficiencia": "tipo_deficiencia",
    "indtrabintermitente": "indicador_trabalho_intermitente",
    "indtrabparcial": "indicador_trabalho_parcial",
    "salario": "salario_mensal",
    "tamestabjan": "tamanho_estabelecimento_janeiro",
    "indicadoraprendiz": "indicador_aprendiz",
    "origemdainformacao": "origem_informacao",
    "competenciadec": "competencia_declarada",
    "competenciaexc": "competencia_exclusao",
    "indicadordeexclusao": "indicador_exclusao",
    "indicadordeforadoprazo": "indicador_fora_prazo",
    "unidadesalariocodigo": "unidade_salario_codigo",
    "valorsalariofixo": "valor_salario_fixo",
}

UF_CODE_TO_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF", "99": "NI",
}


def normalize_column_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", value)


def normalized_mapping(columns: list[str]) -> dict[str, str]:
    return {column: normalize_column_name(column) for column in columns}


def validate_core_columns(normalized_columns: set[str]) -> set[str]:
    return EXPECTED_CORE - normalized_columns
