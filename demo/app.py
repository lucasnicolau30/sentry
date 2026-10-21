"""Demo Cadastro: um app pequeno (login, CRUD de empresas e CRUD de usuários ligados a elas).

Só biblioteca padrão: `python demo/app.py` sobe em http://127.0.0.1:8800. Existe para ter um
alvo real para o `sentry training` e o `sentry manual`: as telas têm <label>, logo, cor e nome.
Login de exemplo: admin@demo.com / admin123.
"""
import hashlib
import hmac
import html
import os
import re
import secrets
import sqlite3
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

PASTA = Path(__file__).resolve().parent
BANCO = PASTA / "demo.db"
NOME_DO_APP = "Demo Cadastro"
VERDE = "#15803d"
SESSOES: dict[str, int] = {}
TRAVA = threading.Lock()
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
ICONES = {
    "editar": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "excluir": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/>',
    "novo": '<path d="M12 5v14"/><path d="M5 12h14"/>',
    "sair": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
}

CSS = f"""
:root{{--verde:{VERDE};--verde-claro:#dcfce7;--borda:#e5e7eb;--texto:#111827;--mudo:#6b7280;--erro:#b91c1c}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:#fff;color:var(--texto)}}
header{{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;padding:.75rem 1.25rem;border-bottom:3px solid var(--verde)}}
header img{{width:36px;height:36px;border-radius:8px}}
.marca{{display:flex;align-items:center;gap:.6rem;font-weight:700;color:var(--texto);text-decoration:none}}
nav{{display:flex;gap:.25rem;margin-left:auto;flex-wrap:wrap}}
nav a,nav button{{color:var(--texto);text-decoration:none;padding:.4rem .7rem;border-radius:6px;background:none;border:0;font:inherit;cursor:pointer;display:inline-flex;gap:.35rem;align-items:center}}
nav a:hover,nav button:hover,nav a.ativo{{background:var(--verde-claro);color:var(--verde)}}
main{{max-width:960px;margin:0 auto;padding:1.25rem}}
.migalhas{{color:var(--mudo);font-size:.9rem;margin-bottom:1rem}}.migalhas a{{color:var(--verde)}}
h1{{margin:.2rem 0 1rem;font-size:1.5rem}}
.barra{{display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:1rem}}
.tabela{{overflow-x:auto;border:1px solid var(--borda);border-radius:8px}}
table{{width:100%;border-collapse:collapse;min-width:520px}}
th,td{{text-align:left;padding:.65rem .8rem;border-bottom:1px solid var(--borda)}}
th{{background:#f9fafb;font-size:.85rem;color:var(--mudo)}}tr:last-child td{{border-bottom:0}}
.acoes{{display:flex;gap:.4rem;justify-content:flex-end}}
.botao{{display:inline-flex;gap:.4rem;align-items:center;padding:.55rem .95rem;border-radius:6px;border:1px solid var(--verde);background:var(--verde);color:#fff;font:inherit;font-weight:600;cursor:pointer;text-decoration:none}}
.botao:hover{{background:#166534}}
.botao.claro{{background:#fff;color:var(--verde)}}.botao.claro:hover{{background:var(--verde-claro)}}
.botao.perigo{{background:var(--erro);border-color:var(--erro)}}
.icone{{display:inline-flex;padding:.4rem;border-radius:6px;border:1px solid var(--borda);background:#fff;color:var(--texto);cursor:pointer}}
.icone:hover{{border-color:var(--verde);color:var(--verde)}}.icone.perigo:hover{{border-color:var(--erro);color:var(--erro)}}
svg{{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
form.campos{{display:grid;gap:1rem;max-width:460px}}
label{{display:block;font-weight:600;margin-bottom:.25rem}}
input{{width:100%;padding:.6rem .7rem;border:1px solid #9ca3af;border-radius:6px;font:inherit}}
input:focus{{outline:2px solid var(--verde);outline-offset:1px}}
.erro{{color:var(--erro);font-size:.85rem;margin:.25rem 0 0}}
.vazio{{padding:2rem;text-align:center;color:var(--mudo)}}
.toast{{position:fixed;right:1rem;bottom:1rem;padding:.8rem 1.1rem;border-radius:8px;color:#fff;background:var(--verde);box-shadow:0 6px 20px #0003;max-width:90vw}}
.toast.erro-toast{{background:var(--erro)}}
dialog{{border:1px solid var(--borda);border-radius:10px;padding:1.25rem;max-width:min(420px,92vw)}}
dialog::backdrop{{background:#0006}}.dialogo-acoes{{display:flex;gap:.5rem;justify-content:flex-end;margin-top:1rem}}
.login{{max-width:420px;margin:3rem auto}}
.busca{{display:flex;gap:.5rem;margin-bottom:1rem}}.busca input{{flex:1}}
"""


def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def hash_da_senha(senha: str, sal: bytes | None = None) -> str:
    sal = sal or secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, 120_000)
    return f"{sal.hex()}${derivada.hex()}"


def senha_confere(senha: str, guardada: str) -> bool:
    sal, _ = guardada.split("$")
    return hmac.compare_digest(hash_da_senha(senha, bytes.fromhex(sal)), guardada)


def preparar_banco() -> None:
    with conectar() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY, nome TEXT NOT NULL, cnpj TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY, nome TEXT NOT NULL, sobrenome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE, senha TEXT NOT NULL,
                empresa_id INTEGER NOT NULL REFERENCES empresas(id));
        """)
        if not con.execute("SELECT 1 FROM usuarios").fetchone():
            empresa = con.execute("INSERT INTO empresas (nome, cnpj) VALUES (?, ?)",
                                  ("Sentry Labs", "12345678000190")).lastrowid
            con.execute("INSERT INTO usuarios (nome, sobrenome, email, senha, empresa_id) VALUES (?,?,?,?,?)",
                        ("Admin", "Demo", "admin@demo.com", hash_da_senha("admin123"), empresa))


def esc(valor) -> str:
    return html.escape(str(valor if valor is not None else ""), quote=True)


def icone(nome: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONES[nome]}</svg>'


def pagina(titulo: str, corpo: str, usuario=None, ativo: str = "", toast: tuple[str, str] | None = None) -> str:
    nav = ""
    if usuario:
        nav = (f'<nav><a href="/empresas" class="{"ativo" if ativo == "empresas" else ""}">Empresas</a>'
               f'<a href="/usuarios" class="{"ativo" if ativo == "usuarios" else ""}">Usuários</a>'
               f'<form method="post" action="/sair"><button type="submit">{icone("sair")} Sair</button></form></nav>')
    aviso = ""
    if toast:
        classe = "toast erro-toast" if toast[0] == "erro" else "toast"
        aviso = (f'<div class="{classe}" role="status">{esc(toast[1])}</div>'
                 '<script>setTimeout(()=>document.querySelector(".toast")?.remove(),4000)</script>')
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} · {NOME_DO_APP}</title>
<meta name="application-name" content="{NOME_DO_APP}">
<meta name="theme-color" content="{VERDE}">
<link rel="icon" type="image/png" href="/static/logo.png">
<style>{CSS}</style></head><body>
<header><a class="marca" href="/"><img src="/static/logo.png" alt="Logo">{NOME_DO_APP}</a>{nav}</header>
<main>{corpo}</main>{aviso}</body></html>"""


def migalhas(*itens: tuple[str, str | None]) -> str:
    partes = [f'<a href="{href}">{esc(texto)}</a>' if href else esc(texto) for texto, href in itens]
    return f'<div class="migalhas">{" / ".join(partes)}</div>'


def campo(id_: str, rotulo: str, valor: str = "", erro: str = "", tipo: str = "text", extra: str = "") -> str:
    msg = f'<p class="erro" id="erro-{id_}">{esc(erro)}</p>' if erro else ""
    return (f'<div><label for="{id_}">{esc(rotulo)}</label>'
            f'<input id="{id_}" name="{id_}" type="{tipo}" value="{esc(valor)}" {extra}>{msg}</div>')


def modal_de_exclusao(entidade: str) -> str:
    return f"""<dialog id="confirmar"><form method="post" id="form-excluir">
<h2 style="margin-top:0">Excluir {entidade}?</h2><p id="texto-excluir"></p>
<div class="dialogo-acoes"><button type="button" class="botao claro" id="cancelar">Cancelar</button>
<button type="submit" class="botao perigo" id="confirmar-exclusao">Excluir {entidade}</button></div></form></dialog>
<script>
const dlg=document.getElementById("confirmar");
document.querySelectorAll("[data-excluir]").forEach(b=>b.addEventListener("click",()=>{{
  document.getElementById("form-excluir").action=b.dataset.excluir;
  document.getElementById("texto-excluir").textContent="Isso remove "+b.dataset.nome+" e não pode ser desfeito.";
  dlg.showModal();}}));
document.getElementById("cancelar").addEventListener("click",()=>dlg.close());
</script>"""


def somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def formatar_cnpj(digitos: str) -> str:
    d = somente_digitos(digitos)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if len(d) == 14 else digitos


class Rejeitado(Exception):
    """Erro de validação ou de regra: leva a mensagem por campo (ou geral) de volta ao formulário."""

    def __init__(self, erros: dict[str, str]):
        super().__init__("; ".join(erros.values()))
        self.erros = erros


def validar_empresa(dados: dict) -> dict:
    erros, limpo = {}, {"nome": dados.get("nome", "").strip(), "cnpj": somente_digitos(dados.get("cnpj", ""))}
    if not limpo["nome"]:
        erros["nome"] = "Informe o nome da empresa."
    if len(limpo["cnpj"]) != 14:
        erros["cnpj"] = "O CNPJ precisa ter 14 dígitos."
    if erros:
        raise Rejeitado(erros)
    return limpo


def validar_usuario(dados: dict, con: sqlite3.Connection, *, senha_obrigatoria: bool) -> dict:
    erros = {}
    limpo = {c: dados.get(c, "").strip() for c in ("nome", "sobrenome", "email", "empresa")}
    limpo["senha"] = dados.get("senha", "")
    for chave, rotulo in (("nome", "o nome"), ("sobrenome", "o sobrenome")):
        if not limpo[chave]:
            erros[chave] = f"Informe {rotulo}."
    if not EMAIL.fullmatch(limpo["email"]):
        erros["email"] = "Informe um e-mail válido."
    if senha_obrigatoria or limpo["senha"]:
        if len(limpo["senha"]) < 6:
            erros["senha"] = "A senha precisa ter ao menos 6 caracteres."
    empresa = con.execute("SELECT id FROM empresas WHERE nome = ?", (limpo["empresa"],)).fetchone()
    if not empresa:
        erros["empresa"] = "Escolha uma empresa cadastrada."
    if erros:
        raise Rejeitado(erros)
    limpo["empresa_id"] = empresa["id"]
    return limpo


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    # ---- infraestrutura -------------------------------------------------
    def usuario_logado(self):
        biscoito = SimpleCookie(self.headers.get("Cookie", ""))
        token = biscoito["sessao"].value if "sessao" in biscoito else None
        uid = SESSOES.get(token)
        if uid is None:
            return None
        with conectar() as con:
            return con.execute("SELECT * FROM usuarios WHERE id = ?", (uid,)).fetchone()

    def toast_pendente(self):
        biscoito = SimpleCookie(self.headers.get("Cookie", ""))
        if "aviso" not in biscoito:
            return None
        tipo, _, texto = unquote(biscoito["aviso"].value).partition("|")
        return tipo, texto

    def responder(self, status: int, corpo: str, cabecalhos=()):
        dados = corpo.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        for nome, valor in cabecalhos:
            self.send_header(nome, valor)
        if self.toast_pendente():
            self.send_header("Set-Cookie", "aviso=; Max-Age=0; Path=/")
        self.end_headers()
        self.wfile.write(dados)

    def redirecionar(self, destino: str, aviso: tuple[str, str] | None = None, cabecalhos=()):
        self.send_response(303)
        self.send_header("Location", destino)
        if aviso:
            self.send_header("Set-Cookie", f"aviso={quote(aviso[0] + '|' + aviso[1])}; Path=/; Max-Age=30")
        for nome, valor in cabecalhos:
            self.send_header(nome, valor)
        self.end_headers()

    def corpo_do_form(self) -> dict:
        tamanho = int(self.headers.get("Content-Length", 0))
        bruto = parse_qs(self.rfile.read(tamanho).decode(), keep_blank_values=True)
        return {chave: valores[0] for chave, valores in bruto.items()}

    def despachar(self, metodo: str):
        caminho = urlparse(self.path).path.rstrip("/") or "/"
        if metodo == "GET" and caminho == "/static/logo.png":
            dados = (PASTA / "static" / "logo.png").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)
            return
        if caminho == "/login":
            return self.login(metodo)
        usuario = self.usuario_logado()
        if usuario is None:
            return self.redirecionar("/login")
        if metodo == "POST" and caminho == "/sair":
            return self.sair()
        if caminho == "/":
            return self.redirecionar("/empresas")
        for rota, tratador in ROTAS:
            achou = re.fullmatch(rota, caminho)
            if achou and metodo in tratador.__dict__.get("metodos", ("GET", "POST")):
                try:
                    return tratador(self, metodo, usuario, *achou.groups())
                except Rejeitado as erro:
                    return tratador(self, "ERRO", usuario, *achou.groups(), erros=erro.erros)
        self.responder(404, pagina("Não encontrado", "<h1>Página não encontrada</h1>", usuario))

    def do_GET(self):
        self.despachar("GET")

    def do_POST(self):
        self.despachar("POST")

    # ---- login ----------------------------------------------------------
    def login(self, metodo: str):
        erro, email = "", ""
        if metodo == "POST":
            dados = self.corpo_do_form()
            email = dados.get("email", "").strip()
            with conectar() as con:
                achado = con.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            if achado and senha_confere(dados.get("senha", ""), achado["senha"]):
                token = secrets.token_urlsafe(24)
                with TRAVA:
                    SESSOES[token] = achado["id"]
                return self.redirecionar("/empresas", ("ok", f"Bem-vindo, {achado['nome']}!"),
                                         [("Set-Cookie", f"sessao={token}; Path=/; HttpOnly; SameSite=Lax")])
            erro = "E-mail ou senha incorretos."
        corpo = (f'<div class="login"><h1>Entrar</h1><form method="post" class="campos">'
                 f'{campo("email", "E-mail de acesso", email, "", "email", "autocomplete=username")}'
                 f'{campo("senha", "Senha de acesso", "", erro, "password", "autocomplete=current-password")}'
                 f'<button class="botao" id="entrar" type="submit">Entrar</button></form></div>')
        self.responder(401 if erro else 200, pagina("Entrar", corpo, toast=self.toast_pendente()))

    def sair(self):
        biscoito = SimpleCookie(self.headers.get("Cookie", ""))
        with TRAVA:
            SESSOES.pop(biscoito["sessao"].value, None)
        self.redirecionar("/login", ("ok", "Você saiu."), [("Set-Cookie", "sessao=; Max-Age=0; Path=/")])


def metodos(*nomes):
    def marcar(funcao):
        funcao.metodos = nomes
        return funcao
    return marcar


# ---- empresas -------------------------------------------------------------
def lista_de_empresas(h: Handler, metodo: str, usuario, erros=None):
    busca = parse_qs(urlparse(h.path).query).get("q", [""])[0].strip()
    with conectar() as con:
        linhas = con.execute("""SELECT e.*, COUNT(u.id) AS pessoas FROM empresas e
                                LEFT JOIN usuarios u ON u.empresa_id = e.id WHERE e.nome LIKE ?
                                GROUP BY e.id ORDER BY e.nome""", (f"%{busca}%",)).fetchall()
    corpo_tabela = "".join(
        f'<tr><td>{esc(e["nome"])}</td><td>{esc(formatar_cnpj(e["cnpj"]))}</td><td>{e["pessoas"]}</td>'
        f'<td><div class="acoes"><a class="icone" href="/empresas/{e["id"]}/editar" title="Editar empresa" aria-label="Editar {esc(e["nome"])}">{icone("editar")}</a>'
        f'<button type="button" class="icone perigo" title="Excluir empresa" aria-label="Excluir {esc(e["nome"])}" '
        f'data-excluir="/empresas/{e["id"]}/excluir" data-nome="{esc(e["nome"])}">{icone("excluir")}</button></div></td></tr>'
        for e in linhas) or '<tr><td colspan="4" class="vazio">Nenhuma empresa cadastrada.</td></tr>'
    corpo = (f'{migalhas(("Empresas", None))}<div class="barra"><h1>Empresas</h1>'
             f'<a class="botao" id="nova-empresa" href="/empresas/nova">{icone("novo")} Nova empresa</a></div>'
             f'<form method="get" role="search" class="busca"><input id="busca" name="q" type="search" '
             f'value="{esc(busca)}" aria-label="Buscar empresa" placeholder="Buscar empresa pelo nome">'
             f'<button class="botao claro" id="buscar" type="submit">Buscar</button></form>'
             f'<div class="tabela"><table><thead><tr><th>Nome</th><th>CNPJ</th><th>Usuários</th><th></th></tr></thead>'
             f'<tbody>{corpo_tabela}</tbody></table></div>{modal_de_exclusao("empresa")}')
    h.responder(200, pagina("Empresas", corpo, usuario, "empresas", h.toast_pendente()))


def formulario_de_empresa(h: Handler, metodo: str, usuario, id_: str | None = None, erros=None):
    with conectar() as con:
        atual = con.execute("SELECT * FROM empresas WHERE id = ?", (id_,)).fetchone() if id_ else None
        if id_ and not atual:
            return h.redirecionar("/empresas", ("erro", "Empresa não encontrada."))
        dados = dict(atual) if atual else {"nome": "", "cnpj": ""}
        if metodo in ("POST", "ERRO"):
            dados = h.corpo_do_form() if metodo == "POST" else getattr(h, "_ultimo_form", dados)
        if metodo == "POST":
            h._ultimo_form = dados
            try:
                limpo = validar_empresa(dados)
                if id_:
                    con.execute("UPDATE empresas SET nome = ?, cnpj = ? WHERE id = ?", (limpo["nome"], limpo["cnpj"], id_))
                else:
                    con.execute("INSERT INTO empresas (nome, cnpj) VALUES (?, ?)", (limpo["nome"], limpo["cnpj"]))
                con.commit()
                return h.redirecionar("/empresas", ("ok", "Empresa salva com sucesso."))
            except sqlite3.IntegrityError:
                raise Rejeitado({"cnpj": "Já existe uma empresa com este CNPJ."}) from None
    erros = erros or {}
    titulo = "Editar empresa" if id_ else "Nova empresa"
    corpo = (f'{migalhas(("Empresas", "/empresas"), (titulo, None))}<h1>{titulo}</h1>'
             f'<form method="post" class="campos">{campo("nome", "Nome da empresa", dados["nome"], erros.get("nome", ""))}'
             f'{campo("cnpj", "CNPJ", dados["cnpj"], erros.get("cnpj", ""), extra="inputmode=numeric")}'
             f'<div><button class="botao" id="salvar" type="submit">Salvar empresa</button> '
             f'<a class="botao claro" href="/empresas">Cancelar</a></div></form>')
    h.responder(422 if erros else 200, pagina(titulo, corpo, usuario, "empresas",
                                              ("erro", "Corrija os campos destacados.") if erros else None))


def excluir_empresa(h: Handler, metodo: str, usuario, id_: str, erros=None):
    with conectar() as con:
        try:
            con.execute("DELETE FROM empresas WHERE id = ?", (id_,))
            con.commit()
        except sqlite3.IntegrityError:
            return h.redirecionar("/empresas", ("erro", "Há usuários ligados a esta empresa; mova-os antes de excluir."))
    h.redirecionar("/empresas", ("ok", "Empresa excluída."))


# ---- usuários ---------------------------------------------------------------
def lista_de_usuarios(h: Handler, metodo: str, usuario, erros=None):
    with conectar() as con:
        linhas = con.execute("""SELECT u.*, e.nome AS empresa FROM usuarios u
                                JOIN empresas e ON e.id = u.empresa_id ORDER BY u.nome""").fetchall()
    corpo_tabela = "".join(
        f'<tr><td>{esc(u["nome"])} {esc(u["sobrenome"])}</td><td>{esc(u["email"])}</td><td>{esc(u["empresa"])}</td>'
        f'<td><div class="acoes"><a class="icone" href="/usuarios/{u["id"]}/editar" title="Editar usuário" aria-label="Editar {esc(u["nome"])}">{icone("editar")}</a>'
        f'<button type="button" class="icone perigo" title="Excluir usuário" aria-label="Excluir {esc(u["nome"])}" '
        f'data-excluir="/usuarios/{u["id"]}/excluir" data-nome="{esc(u["nome"])} {esc(u["sobrenome"])}">{icone("excluir")}</button></div></td></tr>'
        for u in linhas)
    corpo = (f'{migalhas(("Usuários", None))}<div class="barra"><h1>Usuários</h1>'
             f'<a class="botao" id="novo-usuario" href="/usuarios/novo">{icone("novo")} Novo usuário</a></div>'
             f'<div class="tabela"><table><thead><tr><th>Nome</th><th>E-mail</th><th>Empresa</th><th></th></tr></thead>'
             f'<tbody>{corpo_tabela}</tbody></table></div>{modal_de_exclusao("usuário")}')
    h.responder(200, pagina("Usuários", corpo, usuario, "usuarios", h.toast_pendente()))


def formulario_de_usuario(h: Handler, metodo: str, usuario, id_: str | None = None, erros=None):
    with conectar() as con:
        atual = con.execute("""SELECT u.*, e.nome AS empresa FROM usuarios u JOIN empresas e ON e.id = u.empresa_id
                               WHERE u.id = ?""", (id_,)).fetchone() if id_ else None
        if id_ and not atual:
            return h.redirecionar("/usuarios", ("erro", "Usuário não encontrado."))
        dados = dict(atual) if atual else {"nome": "", "sobrenome": "", "email": "", "empresa": ""}
        dados["senha"] = ""
        if metodo == "POST":
            dados = h.corpo_do_form()
            h._ultimo_form = dados
            try:
                limpo = validar_usuario(dados, con, senha_obrigatoria=not id_)
                if id_:
                    con.execute("UPDATE usuarios SET nome=?, sobrenome=?, email=?, empresa_id=? WHERE id=?",
                                (limpo["nome"], limpo["sobrenome"], limpo["email"], limpo["empresa_id"], id_))
                    if limpo["senha"]:
                        con.execute("UPDATE usuarios SET senha=? WHERE id=?", (hash_da_senha(limpo["senha"]), id_))
                else:
                    con.execute("INSERT INTO usuarios (nome, sobrenome, email, senha, empresa_id) VALUES (?,?,?,?,?)",
                                (limpo["nome"], limpo["sobrenome"], limpo["email"],
                                 hash_da_senha(limpo["senha"]), limpo["empresa_id"]))
                con.commit()
                return h.redirecionar("/usuarios", ("ok", "Usuário salvo com sucesso."))
            except sqlite3.IntegrityError:
                raise Rejeitado({"email": "Já existe um usuário com este e-mail."}) from None
        elif metodo == "ERRO":
            dados = getattr(h, "_ultimo_form", dados)
        opcoes = "".join(f'<option value="{esc(e["nome"])}">' for e in con.execute("SELECT nome FROM empresas ORDER BY nome"))
    erros = erros or {}
    titulo = "Editar usuário" if id_ else "Novo usuário"
    dica_senha = " (deixe em branco para manter)" if id_ else ""
    corpo = (f'{migalhas(("Usuários", "/usuarios"), (titulo, None))}<h1>{titulo}</h1>'
             f'<form method="post" class="campos">{campo("nome", "Nome", dados["nome"], erros.get("nome", ""))}'
             f'{campo("sobrenome", "Sobrenome", dados["sobrenome"], erros.get("sobrenome", ""))}'
             f'{campo("email", "E-mail", dados["email"], erros.get("email", ""), "email")}'
             f'{campo("senha", "Senha" + dica_senha, "", erros.get("senha", ""), "password", "autocomplete=new-password")}'
             f'{campo("empresa", "Empresa", dados["empresa"], erros.get("empresa", ""), extra="list=empresas-lista autocomplete=off")}'
             f'<datalist id="empresas-lista">{opcoes}</datalist>'
             f'<div><button class="botao" id="salvar" type="submit">Salvar usuário</button> '
             f'<a class="botao claro" href="/usuarios">Cancelar</a></div></form>')
    h.responder(422 if erros else 200, pagina(titulo, corpo, usuario, "usuarios", ("erro", "Corrija os campos destacados.") if erros else None))


def excluir_usuario(h: Handler, metodo: str, usuario, id_: str, erros=None):
    if str(usuario["id"]) == id_:
        return h.redirecionar("/usuarios", ("erro", "Você não pode excluir o próprio usuário."))
    with conectar() as con:
        con.execute("DELETE FROM usuarios WHERE id = ?", (id_,))
        con.commit()
    h.redirecionar("/usuarios", ("ok", "Usuário excluído."))


ROTAS = [
    (r"/empresas", lista_de_empresas),
    (r"/empresas/nova", formulario_de_empresa),
    (r"/empresas/(\d+)/editar", formulario_de_empresa),
    (r"/empresas/(\d+)/excluir", metodos("POST")(excluir_empresa)),
    (r"/usuarios", lista_de_usuarios),
    (r"/usuarios/novo", formulario_de_usuario),
    (r"/usuarios/(\d+)/editar", formulario_de_usuario),
    (r"/usuarios/(\d+)/excluir", metodos("POST")(excluir_usuario)),
]


def main():
    preparar_banco()
    porta = int(os.environ.get("DEMO_PORT", "8800"))
    print(f"{NOME_DO_APP} em http://127.0.0.1:{porta}  (admin@demo.com / admin123)")
    ThreadingHTTPServer(("127.0.0.1", porta), Handler).serve_forever()


if __name__ == "__main__":
    main()
