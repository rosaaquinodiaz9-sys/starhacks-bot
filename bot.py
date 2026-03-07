import telebot, sqlite3, random, string, json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from datetime import datetime

TOKEN = "8786999967:AAEroloekTowptAPq9TcfqLTYqq_uCVXAFw"
ADMIN_ID = 6694632981
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("store.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, saldo REAL DEFAULT 0, gastado REAL DEFAULT 0, logueado INTEGER DEFAULT 0, login TEXT, password TEXT, es_vip INTEGER DEFAULT 0)""")
cur.execute("""CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, producto TEXT, precio REAL, fecha TEXT, key_codigo TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, plataforma TEXT, dias INTEGER, precio REAL, usada INTEGER DEFAULT 0, user_id INTEGER DEFAULT 0)""")
cur.execute("""CREATE TABLE IF NOT EXISTS recargas (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, monto REAL, metodo TEXT, estado TEXT DEFAULT 'pendiente', fecha TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, tipo TEXT, monto REAL, fecha TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE)""")
cur.execute("""CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, clave TEXT UNIQUE, valor TEXT)""")
conn.commit()

try:
    cur.execute("ALTER TABLE usuarios ADD COLUMN es_vip INTEGER DEFAULT 0")
    conn.commit()
except:
    pass

PRODUCTOS_DEFECTO = {
    "ANDROID ROOT": {
        "HG CHEATS": {"1": "3", "7": "9", "15": "12", "30": "18"},
        "STRICKS BR": {"1": "3", "7": "6", "15": "10", "30": "14"},
        "XTFFHAX": {"1": "3", "7": "7", "15": "11", "30": "16"},
        "BR MODS": {"1": "3", "7": "5", "15": "9", "30": "14"},
        "FzTEAM": {"1": "3", "7": "9", "15": "12", "30": "17"},
    },
    "ANDROID": {
        "HG CHEATS": {"1": "3", "7": "8", "15": "12", "30": "15"},
        "DRIP CLIENT": {"1": "3", "7": "8", "15": "12", "30": "15"},
    },
    "PC": {
        "LX PROYECTO": {"1": "2", "3": "3", "7": "6", "15": "10", "30": "15", "90": "25", "365": "50"},
    }
}

PAISES_DEFECTO = {
    "🇨🇴 Colombia": {"metodo": "NEQUI", "titular": "Miguel Lindo", "numero": "3137997112"},
    "🇪🇨 Ecuador": {"metodo": "BANCO PICHINCHA", "titular": "Holger Gonzales", "numero": "2206205445"},
    "🇪🇸 España": {"metodo": "BBVA", "titular": "Juan Garcia", "numero": "ES1234567890123456"},
    "🇺🇸 USA": {"metodo": "ZELLE", "titular": "Yeckson Gomez", "numero": "2399408946"},
    "🇲🇽 Mexico": {"metodo": "BBVA MEXICO (OXXO)", "titular": "David Pena", "numero": "4152314556767013"},
    "🇵🇪 Peru": {"metodo": "YAPE", "titular": "Jaime Guevara", "numero": "928574897"},
    "🇨🇱 Chile": {"metodo": "CUENTA RUT", "titular": "Carlos Fuenzalida", "numero": "23710151-0"},
    "🇭🇳 Honduras": {"metodo": "BAMPAIS", "titular": "Guillermo Herrera", "numero": "216400100524"},
    "🇦🇷 Argentina": {"metodo": "UALA", "titular": "Cesar Correa", "alias": "c.correa1315.uala"},
    "💎 Binance USDT": {"metodo": "BINANCE", "titular": "MrFrancisofficial", "numero": "1140248187"},
}

RANGOS = [
    {"nombre": "USUARIO", "min": 0, "max": 49, "desc": 0},
    {"nombre": "VIP", "min": 50, "max": 149, "desc": 5},
    {"nombre": "PREMIUM", "min": 150, "max": 249, "desc": 10},
    {"nombre": "DIAMOND", "min": 250, "max": 499, "desc": 15},
    {"nombre": "DELUXE", "min": 500, "max": 99999999, "desc": 20},
]

SESION = {}

def set_paso(uid, paso, datos={}):
    SESION[uid] = {"paso": paso, "datos": datos.copy()}

def get_paso(uid):
    return SESION.get(uid, {}).get("paso")

def get_datos(uid):
    return SESION.get(uid, {}).get("datos", {})

def clear_paso(uid):
    SESION.pop(uid, None)

def cargar_config(clave, defecto=None):
    cur.execute("SELECT valor FROM config WHERE clave=?", (clave,))
    r = cur.fetchone()
    if r:
        try:
            return json.loads(r[0])
        except:
            return r[0]
    return defecto

def guardar_config(clave, valor):
    cur.execute("DELETE FROM config WHERE clave=?", (clave,))
    cur.execute("INSERT INTO config (clave, valor) VALUES (?,?)", (clave, json.dumps(valor)))
    conn.commit()

def get_productos():
    return cargar_config("productos", PRODUCTOS_DEFECTO)

def get_paises():
    return cargar_config("paises", PAISES_DEFECTO)

def registrar(user):
    cur.execute("SELECT id FROM usuarios WHERE id=?", (user.id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO usuarios (id, nombre, login, password) VALUES (?,?,?,?)",
                    (user.id, user.first_name.strip(), None, None))
        conn.commit()

def get_user(uid):
    cur.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
    return cur.fetchone()

def es_admin(uid):
    if uid == ADMIN_ID:
        return True
    cur.execute("SELECT user_id FROM admins WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def es_vip(uid):
    u = get_user(uid)
    if not u:
        return False
    try:
        return u[7] == 1
    except:
        return False

def get_rango(gastado):
    for r in RANGOS:
        if r["min"] <= gastado <= r["max"]:
            return r
    return RANGOS[-1]

def edit_msg(call, texto, kb):
    try:
        bot.edit_message_text(texto, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, texto, parse_mode="Markdown", reply_markup=kb)

def menu_sin_login():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔐  L O G I N", callback_data="abrir_login"))
    kb.add(InlineKeyboardButton("📝  C R E A R   L O G I N", callback_data="abrir_crear_login"))
    return kb

def menu_cliente():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🛒 Comprar Key", callback_data="cli_comprar"),
           InlineKeyboardButton("👤 Mi Cuenta", callback_data="cli_cuenta"))
    kb.add(InlineKeyboardButton("📋 Historial Compras", callback_data="cli_historial_compras"),
           InlineKeyboardButton("🔑 Mis Keys", callback_data="cli_mis_keys"))
    kb.add(InlineKeyboardButton("💳 Recargas", callback_data="cli_recargas"),
           InlineKeyboardButton("📜 Historial Recarga", callback_data="cli_historial_recarga"))
    kb.add(InlineKeyboardButton("🏆 Mi Rango", callback_data="cli_mi_rango"),
           InlineKeyboardButton("💬 Soporte", callback_data="cli_soporte"))
    kb.add(InlineKeyboardButton("🌿 Grupo WhatsApp 🍀", url="https://chat.whatsapp.com/FQ1r56CjIa396gT9O8gCWF"))
    kb.add(InlineKeyboardButton("🚀  C E R R A R   S E S I O N", callback_data="cli_cerrar_sesion"))
    return kb

def menu_admin():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("⚙️ Editar Precios", callback_data="admin_editar_precios"),
           InlineKeyboardButton("💳 Agregar Método", callback_data="admin_editar_paises"))
    kb.add(InlineKeyboardButton("👥 Usuarios", callback_data="admin_usuarios"),
           InlineKeyboardButton("💰 Agregar Saldo", callback_data="admin_agregar_saldo"))
    kb.add(InlineKeyboardButton("📦 Agregar Stock", callback_data="admin_agregar_keys"),
           InlineKeyboardButton("📥 Recargas", callback_data="admin_recargas"))
    kb.add(InlineKeyboardButton("🍀 Crear Usuario VIP", callback_data="admin_crear_vip"),
           InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
    kb.add(InlineKeyboardButton("🏷️ Agregar Descuento", callback_data="admin_agregar_descuento"),
           InlineKeyboardButton("📋 Informe Completo", callback_data="admin_informe"))
    kb.add(InlineKeyboardButton("🏠 Menu Cliente", callback_data="admin_menu_cliente"))
    return kb

def menu_categorias():
    kb = InlineKeyboardMarkup(row_width=1)
    for cat in get_productos().keys():
        kb.add(InlineKeyboardButton(cat, callback_data="cat_" + cat))
    kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
    return kb

def menu_productos_kb(cat):
    kb = InlineKeyboardMarkup(row_width=1)
    for p in get_productos()[cat].keys():
        kb.add(InlineKeyboardButton(p, callback_data="prod_" + cat + "_" + p))
    kb.add(InlineKeyboardButton("🔙 Volver", callback_data="cli_comprar"))
    return kb

def menu_dias_compra(cat, prod):
    productos = get_productos()
    kb = InlineKeyboardMarkup(row_width=2)
    for dias, precio in productos[cat][prod].items():
        cur.execute("SELECT COUNT(*) FROM keys WHERE plataforma=? AND dias=? AND usada=0",
                    (cat + "-" + prod, int(dias)))
        stock = cur.fetchone()[0]
        if stock > 0:
            kb.add(InlineKeyboardButton(dias + "d -> $" + precio + " [" + str(stock) + " disp]",
                                         callback_data="buy_" + cat + "_" + prod + "_" + dias + "_" + precio))
        else:
            kb.add(InlineKeyboardButton("❌ " + dias + "d -> SIN STOCK",
                                         callback_data="sin_stock"))
    kb.add(InlineKeyboardButton("🔙 Volver", callback_data="cat_" + cat))
    return kb

def menu_paises_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    for pais in get_paises().keys():
        kb.add(InlineKeyboardButton(pais, callback_data="pais_" + pais))
    kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    registrar(msg.from_user)
    if not cargar_config("productos"):
        guardar_config("productos", PRODUCTOS_DEFECTO)
    if not cargar_config("paises"):
        guardar_config("paises", PAISES_DEFECTO)
    uid = msg.from_user.id
    clear_paso(uid)
    nombre = msg.from_user.first_name
    bot.send_message(msg.chat.id, ".", reply_markup=ReplyKeyboardRemove())
    bienvenida = (
        "🌿 *FzTeam Socios* 🍀\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "👋 Hola *" + nombre + "*\n\n"
        "🔥 Bot oficial de venta de mods premium\n\n"
        "👑 Admin: @Fr4ncisOfficial\n\n"
        "━━━━━━━━━━━━━━━━"
    )
    if es_admin(uid):
        bot.send_message(msg.chat.id, bienvenida, parse_mode="Markdown", reply_markup=menu_admin())
    else:
        bot.send_message(msg.chat.id, bienvenida, parse_mode="Markdown", reply_markup=menu_sin_login())

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def manejar_texto(msg):
    uid = msg.from_user.id
    paso = get_paso(uid)
    texto = msg.text.strip()

    if paso is None:
        return

    if paso == "login_user":
        set_paso(uid, "login_pass", {"login": texto})
        bot.send_message(msg.chat.id, "🔐 Escribe tu contrasena:")

    elif paso == "login_pass":
        login_in = get_datos(uid).get("login", "")
        clear_paso(uid)
        cur.execute("SELECT id FROM usuarios WHERE login=? AND password=?", (login_in, texto))
        if cur.fetchone():
            cur.execute("UPDATE usuarios SET logueado=1 WHERE id=?", (uid,))
            conn.commit()
            u = get_user(uid)
            login_nombre = u[5] or u[1]
            if es_admin(uid):
                bot.send_message(msg.chat.id,
                    "✅ *BIENVENIDO " + login_nombre.upper() + "* 👑",
                    parse_mode="Markdown", reply_markup=menu_admin())
            else:
                vip_tag = " 🍀 *VIP*" if es_vip(uid) else ""
                bot.send_message(msg.chat.id,
                    "🌿 *FzTeam Socios* 🍀\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "👤 Soy *" + login_nombre + "*" + vip_tag + "\n"
                    "🛡️ Compra tus keys seguras conmigo!\n\n"
                    "✅ Tu exito es nuestra prioridad.\n\n"
                    "━━━━━━━━━━━━━━━━",
                    parse_mode="Markdown", reply_markup=menu_cliente())
        else:
            bot.send_message(msg.chat.id, "❌ Usuario o contrasena incorrectos.",
                             reply_markup=menu_sin_login())

    elif paso == "crear_user":
        if len(texto) < 3 or len(texto) > 20:
            bot.send_message(msg.chat.id, "❌ Entre 3 y 20 caracteres:")
            return
        cur.execute("SELECT id FROM usuarios WHERE login=?", (texto,))
        if cur.fetchone():
            bot.send_message(msg.chat.id, "❌ Ya existe. Escribe otro:")
            return
        set_paso(uid, "crear_pass", {"login": texto})
        bot.send_message(msg.chat.id, "✅ Usuario: *" + texto + "*\n\n🔐 Contrasena (4-20 caracteres):",
                         parse_mode="Markdown")

    elif paso == "crear_pass":
        login = get_datos(uid).get("login", "")
        if not login:
            clear_paso(uid)
            bot.send_message(msg.chat.id, "❌ Error. Usa /start", reply_markup=menu_sin_login())
            return
        if len(texto) < 4 or len(texto) > 20:
            bot.send_message(msg.chat.id, "❌ Entre 4 y 20 caracteres:")
            return
        cur.execute("UPDATE usuarios SET login=?, password=? WHERE id=?", (login, texto, uid))
        conn.commit()
        clear_paso(uid)
        bot.send_message(msg.chat.id,
                         "✅ *CUENTA CREADA*\n\n👤 `" + login + "`\n🔐 `" + texto + "`\n\nAhora inicia sesion:",
                         parse_mode="Markdown", reply_markup=menu_sin_login())

    elif paso == "recarga":
        pais = get_datos(uid).get("pais", "")
        try:
            monto = float(texto)
            if monto < 5:
                bot.send_message(msg.chat.id, "❌ Minimo $5 USD:")
                return
            u = get_user(uid)
            cur.execute("INSERT INTO recargas VALUES (NULL,?,?,?,?,?)",
                        (uid, monto, pais, "pendiente", datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            rid = cur.lastrowid
            clear_paso(uid)
            bot.send_message(msg.chat.id, "📊 *Solicitud enviada*\n💳 " + pais + "\n💰 $" + str(monto),
                             parse_mode="Markdown", reply_markup=menu_cliente())
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Aprobar", callback_data="aprob_" + str(rid)),
                   InlineKeyboardButton("❌ Rechazar", callback_data="rech_" + str(rid)))
            bot.send_message(ADMIN_ID, "💳 *RECARGA*\n👤 " + u[1] + "\n💰 $" + str(monto) + "\n🌍 " + pais,
                             parse_mode="Markdown", reply_markup=kb)
        except:
            bot.send_message(msg.chat.id, "❌ Solo el numero. Ejemplo: 10")

    elif paso == "soporte":
        clear_paso(uid)
        bot.send_message(ADMIN_ID,
                         "📞 *SOPORTE*\n👤 " + msg.from_user.first_name + "\n🆔 " + str(uid) + "\n\n💬 " + msg.text,
                         parse_mode="Markdown")
        bot.send_message(msg.chat.id, "✅ Mensaje enviado.", reply_markup=menu_cliente())

    elif paso == "agregar_saldo":
        try:
            parts = texto.split()
            tid = int(parts[0])
            monto = float(parts[1])
            u = get_user(tid)
            if not u:
                bot.send_message(msg.chat.id, "❌ Usuario no encontrado:")
                return
            nuevo = round(u[2] + monto, 2)
            cur.execute("UPDATE usuarios SET saldo=? WHERE id=?", (nuevo, tid))
            cur.execute("INSERT INTO movimientos VALUES (NULL,?,?,?,?)",
                        (tid, "recarga", monto, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            clear_paso(uid)
            bot.send_message(msg.chat.id, "✅ +$" + str(monto) + " a " + u[1] + "\n💳 $" + str(nuevo), reply_markup=menu_admin())
            bot.send_message(tid, "💰 *+$" + str(monto) + "*\n💳 Saldo: $" + str(nuevo), parse_mode="Markdown")
        except:
            bot.send_message(msg.chat.id, "❌ Formato: 123456789 50")

    elif paso == "crear_vip":
        try:
            tid = int(texto)
            u = get_user(tid)
            if not u:
                bot.send_message(msg.chat.id, "❌ Usuario no encontrado:")
                return
            cur.execute("UPDATE usuarios SET es_vip=1 WHERE id=?", (tid,))
            conn.commit()
            clear_paso(uid)
            bot.send_message(msg.chat.id, "🍀 *VIP asignado a " + u[1] + "*",
                             parse_mode="Markdown", reply_markup=menu_admin())
            bot.send_message(tid, "🍀 *Eres VIP ahora!*\nDisfruta tus beneficios exclusivos.",
                             parse_mode="Markdown")
        except:
            bot.send_message(msg.chat.id, "❌ ID invalido:")

    elif paso == "agregar_descuento":
        try:
            parts = texto.split()
            tid = int(parts[0])
            descuento = int(parts[1])
            u = get_user(tid)
            if not u:
                bot.send_message(msg.chat.id, "❌ Usuario no encontrado:")
                return
            descuentos = cargar_config("descuentos_usuarios", {})
            descuentos[str(tid)] = descuento
            guardar_config("descuentos_usuarios", descuentos)
            clear_paso(uid)
            bot.send_message(msg.chat.id, "🏷️ Descuento del " + str(descuento) + "% asignado a " + u[1],
                             reply_markup=menu_admin())
            bot.send_message(tid, "🏷️ *Tienes un descuento especial del " + str(descuento) + "%!*",
                             parse_mode="Markdown")
        except:
            bot.send_message(msg.chat.id, "❌ Formato: ID PORCENTAJE\nEjemplo: 123456789 15")

    elif paso == "agregar_keys":
        datos = get_datos(uid)
        plataforma = datos.get("plataforma", "")
        dias = datos.get("dias", 1)
        clear_paso(uid)
        count = 0
        duplicadas = 0
        for linea in msg.text.strip().split("\n"):
            codigo = linea.strip()
            if codigo:
                try:
                    cur.execute("INSERT INTO keys VALUES (NULL,?,?,?,?,?,?)",
                                (codigo, plataforma, int(dias), 0, 0, 0))
                    count += 1
                except:
                    duplicadas += 1
        conn.commit()
        txt = "✅ *" + str(count) + " keys agregadas*\n📦 " + plataforma + " - " + str(dias) + " dias"
        if duplicadas > 0:
            txt += "\n⚠️ " + str(duplicadas) + " duplicadas ignoradas"
        bot.send_message(msg.chat.id, txt, parse_mode="Markdown", reply_markup=menu_admin())

    elif paso == "edit_precio":
        cat = get_datos(uid).get("cat", "")
        prod = get_datos(uid).get("prod", "")
        clear_paso(uid)
        try:
            productos = get_productos()
            for par in texto.split():
                d2, p2 = par.split(":")
                productos[cat][prod][d2] = p2
            guardar_config("productos", productos)
            bot.send_message(msg.chat.id, "✅ Actualizado", reply_markup=menu_admin())
        except:
            bot.send_message(msg.chat.id, "❌ Formato: 1:3 7:9 15:12 30:18")

    elif paso == "edit_pais":
        pais = get_datos(uid).get("pais", "")
        clear_paso(uid)
        try:
            paises = get_paises()
            p = texto.split("|")
            paises[pais]["metodo"] = p[0].strip()
            paises[pais]["titular"] = p[1].strip()
            paises[pais]["numero"] = p[2].strip()
            guardar_config("paises", paises)
            bot.send_message(msg.chat.id, "✅ " + pais + " actualizado", reply_markup=menu_admin())
        except:
            bot.send_message(msg.chat.id, "❌ Formato: metodo|titular|numero")

    elif paso == "new_pais":
        clear_paso(uid)
        try:
            parts = texto.split("|")
            paises = get_paises()
            paises[parts[0].strip()] = {
                "metodo": parts[1].strip() if len(parts) > 1 else "",
                "titular": parts[2].strip() if len(parts) > 2 else "",
                "numero": parts[3].strip() if len(parts) > 3 else "",
            }
            guardar_config("paises", paises)
            bot.send_message(msg.chat.id, "✅ Metodo de pago agregado", reply_markup=menu_admin())
        except:
            bot.send_message(msg.chat.id, "❌ Formato: NombrePais|metodo|titular|numero")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    registrar(call.from_user)
    uid = call.from_user.id
    d = call.data
    bot.answer_callback_query(call.id)

    if d == "sin_stock":
        bot.answer_callback_query(call.id, "❌ Sin stock disponible", show_alert=True)
        return

    if d == "abrir_login":
        clear_paso(uid)
        set_paso(uid, "login_user")
        bot.send_message(call.message.chat.id, "👤 Escribe tu usuario:")

    elif d == "abrir_crear_login":
        clear_paso(uid)
        set_paso(uid, "crear_user")
        bot.send_message(call.message.chat.id, "📝 Escribe el usuario que quieres (3-20 caracteres):")

    elif d == "volver_cliente":
        edit_msg(call, "👉 *Menu Cliente*", menu_cliente())

    elif d == "volver_admin":
        edit_msg(call, "👉 *Menu Admin*", menu_admin())

    elif d == "cli_comprar":
        edit_msg(call, "🛒 *Elige la categoria:*", menu_categorias())

    elif d == "cli_cuenta":
        u = get_user(uid)
        rango = get_rango(u[3])
        vip_txt = " 🍀 VIP" if es_vip(uid) else ""
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
        edit_msg(call,
                 "👤 *MI CUENTA*\n━━━━━━━━━━━━━━━━\n"
                 "🆔 ID: `" + str(uid) + "`\n"
                 "🧑 Usuario: `" + str(u[5] or "sin login") + "`" + vip_txt + "\n"
                 "💳 Saldo: $" + str(round(u[2], 2)) + "\n"
                 "🛒 Gastado: $" + str(round(u[3], 2)) + "\n"
                 "🏆 Rango: " + rango['nombre'] + "\n"
                 "🏷️ Descuento: " + str(rango['desc']) + "%\n"
                 "━━━━━━━━━━━━━━━━", kb)

    elif d == "cli_historial_compras":
        cur.execute("SELECT producto, precio, fecha, key_codigo FROM compras WHERE user_id=?", (uid,))
        compras = cur.fetchall()
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
        if not compras:
            edit_msg(call, "📋 Sin compras aun.", kb)
        else:
            t = "📋 *COMPRAS*\n━━━━━━━━━━━━━━━━\n\n"
            for p, pr, f, kc in compras:
                t += "✅ " + p + "\n💰 $" + str(pr) + " | 📅 " + f + "\n🔑 `" + str(kc) + "`\n\n"
            edit_msg(call, t, kb)

    elif d == "cli_mis_keys":
        cur.execute("SELECT codigo, plataforma, dias FROM keys WHERE user_id=? AND usada=1", (uid,))
        keys = cur.fetchall()
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
        if not keys:
            edit_msg(call, "🔑 Sin keys aun.", kb)
        else:
            t = "🔑 *TUS KEYS*\n━━━━━━━━━━━━━━━━\n\n"
            for codigo, plat, dias in keys:
                t += "📦 " + plat + " - " + str(dias) + "d\n`" + codigo + "`\n\n"
            edit_msg(call, t, kb)

    elif d == "cli_recargas":
        edit_msg(call, "💰 *Elige tu metodo de pago:*\n\n💵 *Recarga Minima: 5 USD*\n\nEjemplo: 10", menu_paises_kb())

    elif d == "cli_historial_recarga":
        cur.execute("SELECT tipo, monto, fecha FROM movimientos WHERE user_id=?", (uid,))
        movs = cur.fetchall()
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
        if not movs:
            edit_msg(call, "📜 Sin movimientos.", kb)
        else:
            t = "📜 *MOVIMIENTOS*\n━━━━━━━━━━━━━━━━\n\n"
            for tp, m2, f in movs:
                icono = "➕" if tp == "recarga" else "➖"
                t += icono + " " + tp.upper() + " $" + str(m2) + " | " + f + "\n"
            edit_msg(call, t, kb)

    elif d == "cli_mi_rango":
        u = get_user(uid)
        rango = get_rango(u[3])
        idx = RANGOS.index(rango)
        sig = RANGOS[idx+1] if idx+1 < len(RANGOS) else None
        t = "🏆 *" + rango['nombre'] + "*\n🏷️ " + str(rango['desc']) + "% descuento\n💰 Gastado: $" + str(round(u[3],2))
        if sig:
            t += "\n\n⬆️ Siguiente: *" + sig['nombre'] + "*\nFaltan: $" + str(round(sig['min']-u[3],2))
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
        edit_msg(call, t, kb)

    elif d == "cli_soporte":
        set_paso(uid, "soporte")
        bot.send_message(call.message.chat.id, "💬 Escribe tu mensaje:")

    elif d == "cli_cerrar_sesion":
        clear_paso(uid)
        cur.execute("UPDATE usuarios SET logueado=0 WHERE id=?", (uid,))
        conn.commit()
        edit_msg(call, "🔒 *Sesion cerrada*\n\nHasta pronto 👋", menu_sin_login())

    elif d == "admin_menu_cliente":
        edit_msg(call, "👉 *Menu Cliente*", menu_cliente())

    elif d == "admin_informe":
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total_u = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE logueado=1")
        activos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM compras")
        total_c = cur.fetchone()[0]
        cur.execute("SELECT SUM(precio) FROM compras")
        total_v = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM keys WHERE usada=0")
        keys_disp = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM keys WHERE usada=1")
        keys_usadas = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recargas WHERE estado='pendiente'")
        rec_pend = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recargas WHERE estado='aprobada'")
        rec_apro = cur.fetchone()[0]
        cur.execute("SELECT SUM(monto) FROM recargas WHERE estado='aprobada'")
        total_rec = cur.fetchone()[0] or 0
        cur.execute("SELECT plataforma, COUNT(*) as cnt FROM keys WHERE usada=0 GROUP BY plataforma ORDER BY cnt DESC")
        stock_por_prod = cur.fetchall()
        cur.execute("SELECT producto, COUNT(*) as cnt FROM compras GROUP BY producto ORDER BY cnt DESC LIMIT 5")
        top_prod = cur.fetchall()
        cur.execute("SELECT u.nombre, u.gastado FROM usuarios u ORDER BY u.gastado DESC LIMIT 5")
        top_users = cur.fetchall()
        t = (
            "📋 *INFORME COMPLETO*\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "👥 *USUARIOS*\n"
            "Total: " + str(total_u) + " | Con login: " + str(activos) + "\n\n"
            "🛒 *VENTAS*\n"
            "Total compras: " + str(total_c) + "\n"
            "Total vendido: $" + str(round(total_v,2)) + "\n\n"
            "💳 *RECARGAS*\n"
            "Aprobadas: " + str(rec_apro) + " ($" + str(round(total_rec,2)) + ")\n"
            "Pendientes: " + str(rec_pend) + "\n\n"
            "🔑 *KEYS*\n"
            "Disponibles: " + str(keys_disp) + "\n"
            "Usadas: " + str(keys_usadas) + "\n\n"
            "📦 *STOCK POR PRODUCTO*\n"
        )
        for plat, cnt in stock_por_prod:
            t += "• " + str(plat) + ": " + str(cnt) + " keys\n"
        t += "\n🏆 *TOP 5 PRODUCTOS*\n"
        for prod, cnt in top_prod:
            t += "• " + str(prod) + ": " + str(cnt) + " ventas\n"
        t += "\n💎 *TOP 5 CLIENTES*\n"
        for nombre, gastado in top_users:
            t += "• " + str(nombre) + ": $" + str(round(gastado,2)) + "\n"
        t += "\n📅 " + datetime.now().strftime("%Y-%m-%d %H:%M")
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
        edit_msg(call, t, kb)

    elif d == "admin_editar_precios":
        kb = InlineKeyboardMarkup(row_width=1)
        for cat in get_productos().keys():
            kb.add(InlineKeyboardButton(cat, callback_data="edit_cat_" + cat))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
        edit_msg(call, "⚙️ *Categoria:*", kb)

    elif d == "admin_editar_paises":
        kb = InlineKeyboardMarkup(row_width=1)
        for pais in get_paises().keys():
            kb.add(InlineKeyboardButton(pais, callback_data="edit_pais_" + pais))
        kb.add(InlineKeyboardButton("➕ Agregar Metodo", callback_data="add_pais"))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
        edit_msg(call, "💳 *Metodos de Pago:*", kb)

    elif d == "admin_usuarios":
        cur.execute("SELECT id, nombre, saldo, gastado, login FROM usuarios")
        us = cur.fetchall()
        t = "👥 *" + str(len(us)) + " usuarios*\n━━━━━━━━━━━━━━━━\n\n"
        for u in us[:20]:
            login_txt = u[4] or "sin login"
            t += "👤 " + u[1] + " (@" + login_txt + ")\n🆔 `" + str(u[0]) + "` | 💳 $" + str(round(u[2],0)) + " | 🛒 $" + str(round(u[3],0)) + "\n\n"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
        edit_msg(call, t, kb)

    elif d == "admin_agregar_saldo":
        set_paso(uid, "agregar_saldo")
        bot.send_message(call.message.chat.id, "💰 Escribe: ID MONTO\nEjemplo: 123456789 50")

    elif d == "admin_agregar_keys":
        kb = InlineKeyboardMarkup(row_width=1)
        for cat in get_productos().keys():
            kb.add(InlineKeyboardButton(cat, callback_data="addkey_cat_" + cat))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
        edit_msg(call, "📦 *Agregar Stock - Elige categoria:*", kb)

    elif d == "admin_recargas":
        cur.execute("SELECT r.id, u.nombre, r.monto, r.metodo FROM recargas r JOIN usuarios u ON r.user_id=u.id WHERE r.estado='pendiente'")
        recargas = cur.fetchall()
        if not recargas:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
            edit_msg(call, "✅ Sin pendientes", kb)
            return
        for r in recargas:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Aprobar", callback_data="aprob_" + str(r[0])),
                   InlineKeyboardButton("❌ Rechazar", callback_data="rech_" + str(r[0])))
            bot.send_message(call.message.chat.id, "💳 *" + r[1] + "*\n$" + str(r[2]) + " | " + r[3],
                             parse_mode="Markdown", reply_markup=kb)

    elif d == "admin_crear_vip":
        set_paso(uid, "crear_vip")
        bot.send_message(call.message.chat.id, "🍀 Escribe el ID del usuario para hacerlo VIP:")

    elif d == "admin_agregar_descuento":
        set_paso(uid, "agregar_descuento")
        bot.send_message(call.message.chat.id, "🏷️ Escribe: ID PORCENTAJE\nEjemplo: 123456789 15")

    elif d == "admin_stats":
        cur.execute("SELECT COUNT(*) FROM usuarios")
        u = cur.fetchone()[0]
        cur.execute("SELECT SUM(gastado) FROM usuarios")
        v = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM compras")
        c = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recargas WHERE estado='pendiente'")
        p = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM keys WHERE usada=0")
        k = cur.fetchone()[0]
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_admin"))
        edit_msg(call, "📊 *STATS*\n━━━━━━━━━━━━━━━━\n👥 Usuarios: " + str(u) + "\n🛒 Compras: " + str(c) + "\n💰 Vendido: $" + str(round(v,2)) + "\n⏳ Pendientes: " + str(p) + "\n🔑 Keys disp: " + str(k), kb)

    elif d.startswith("cat_"):
        cat = d[4:]
        edit_msg(call, "📦 *" + cat + "*\n\nElige producto:", menu_productos_kb(cat))

    elif d.startswith("prod_"):
        partes = d[5:].split("_")
        cat = partes[0]
        prod = "_".join(partes[1:])
        edit_msg(call, "📦 *" + prod + "*\n\nElige dias:", menu_dias_compra(cat, prod))

    elif d.startswith("buy_"):
        partes = d[4:].split("_")
        cat = partes[0]
        prod = partes[1]
        dias = partes[2]
        precio = float(partes[3])
        u = get_user(uid)
        rango = get_rango(u[3])
        desc = rango['desc']
        descuentos_esp = cargar_config("descuentos_usuarios", {})
        if str(uid) in descuentos_esp:
            desc = max(desc, descuentos_esp[str(uid)])
        pf = round(precio * (1 - desc/100), 2)
        plataforma = cat + "-" + prod
        cur.execute("SELECT id, codigo FROM keys WHERE plataforma=? AND dias=? AND usada=0 LIMIT 1",
                    (plataforma, int(dias)))
        key_row = cur.fetchone()
        if not key_row:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
            edit_msg(call, "❌ *Sin stock disponible*\nContacta al admin.", kb)
            return
        if u[2] >= pf:
            key_id, codigo = key_row
            cur.execute("UPDATE keys SET usada=1, user_id=? WHERE id=?", (uid, key_id))
            ns = round(u[2] - pf, 2)
            ng = round(u[3] + pf, 2)
            cur.execute("UPDATE usuarios SET saldo=?, gastado=? WHERE id=?", (ns, ng, uid))
            cur.execute("INSERT INTO compras VALUES (NULL,?,?,?,?,?)",
                        (uid, plataforma + " " + dias + "d", pf, datetime.now().strftime("%Y-%m-%d"), codigo))
            cur.execute("INSERT INTO movimientos VALUES (NULL,?,?,?,?)",
                        (uid, "compra", pf, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Menu", callback_data="volver_cliente"))
            edit_msg(call,
                     "🎉 *COMPRA EXITOSA!*\n"
                     "━━━━━━━━━━━━━━━━\n"
                     "📦 " + plataforma + "\n"
                     "⏱️ " + dias + " dias\n"
                     "💵 $" + str(pf) + "\n"
                     "🏷️ Descuento: -" + str(desc) + "%\n\n"
                     "🔑 *TU KEY:*\n"
                     "━━━━━━━━━━━━━━━━\n"
                     "`" + codigo + "`\n"
                     "━━━━━━━━━━━━━━━━\n\n"
                     "💳 Saldo restante: $" + str(ns), kb)
        else:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("💳 Recargar", callback_data="cli_recargas"))
            kb.add(InlineKeyboardButton("🔙 Volver", callback_data="volver_cliente"))
            edit_msg(call, "❌ *Saldo insuficiente*\n💳 Tienes: $" + str(round(u[2],2)) + "\n💰 Necesitas: $" + str(pf), kb)

    elif d.startswith("pais_"):
        pais = d[5:]
        datos = get_paises()[pais]
        t = "💳 *" + pais + "*\n━━━━━━━━━━━━━━━━\n\n"
        for k, v in datos.items():
            t += "▪️ *" + k + ":* `" + v + "`\n"
        t += "\n📌 Paga y presiona Ya Pague\n\n💵 *Minimo: $5 USD*"
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("✅ Ya Pague", callback_data="pague_" + pais))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="cli_recargas"))
        edit_msg(call, t, kb)

    elif d.startswith("pague_"):
        pais = d[6:]
        set_paso(uid, "recarga", {"pais": pais})
        bot.send_message(call.message.chat.id,
                         "💰 *Recargar Saldo*\n\n¿Cuanto Deseas Recargar?\n\n💵 *Recarga Minima: 5 USD*\n\nEjemplo: 10",
                         parse_mode="Markdown")

    elif d.startswith("addkey_cat_"):
        cat = d[11:]
        kb = InlineKeyboardMarkup(row_width=1)
        for prod in get_productos()[cat].keys():
            kb.add(InlineKeyboardButton(prod, callback_data="addkey_prod_" + cat + "|" + prod))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="admin_agregar_keys"))
        edit_msg(call, "📦 *" + cat + "*\nElige producto:", kb)

    elif d.startswith("addkey_prod_"):
        partes = d[12:].split("|")
        cat = partes[0]
        prod = partes[1]
        plataforma = cat + "-" + prod
        productos = get_productos()
        kb = InlineKeyboardMarkup(row_width=2)
        for dias in productos[cat][prod].keys():
            cur.execute("SELECT COUNT(*) FROM keys WHERE plataforma=? AND dias=? AND usada=0",
                        (plataforma, int(dias)))
            stock = cur.fetchone()[0]
            kb.add(InlineKeyboardButton(dias + "d [" + str(stock) + " disp]",
                                         callback_data="addkey_dias_" + cat + "|" + prod + "|" + dias))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="addkey_cat_" + cat))
        edit_msg(call, "📦 *" + prod + "*\nElige para cuantos dias son las keys:", kb)

    elif d.startswith("addkey_dias_"):
        partes = d[12:].split("|")
        cat = partes[0]
        prod = partes[1]
        dias = partes[2]
        plataforma = cat + "-" + prod
        set_paso(uid, "agregar_keys", {"plataforma": plataforma, "dias": dias})
        bot.send_message(call.message.chat.id,
                         "📦 *Stock para " + prod + " - " + dias + " dias*\n\nPega las keys, una por linea:",
                         parse_mode="Markdown")

    elif d.startswith("edit_cat_"):
        cat = d[9:]
        kb = InlineKeyboardMarkup(row_width=1)
        for prod in get_productos()[cat].keys():
            kb.add(InlineKeyboardButton(prod, callback_data="edit_prod_" + cat + "|" + prod))
        kb.add(InlineKeyboardButton("🔙 Volver", callback_data="admin_editar_precios"))
        edit_msg(call, "⚙️ *" + cat + "*", kb)

    elif d.startswith("edit_prod_"):
        partes = d[10:].split("|")
        cat = partes[0]
        prod = partes[1]
        set_paso(uid, "edit_precio", {"cat": cat, "prod": prod})
        pa = " ".join([k+":"+v for k, v in get_productos()[cat][prod].items()])
        bot.send_message(call.message.chat.id,
                         "⚙️ *" + prod + "*\nActual: `" + pa + "`\n\nNuevo formato: `1:3 7:9 15:12 30:18`",
                         parse_mode="Markdown")

    elif d.startswith("edit_pais_"):
        pais = d[10:]
        set_paso(uid, "edit_pais", {"pais": pais})
        datos = get_paises().get(pais, {})
        actual = datos.get('metodo','') + "|" + datos.get('titular','') + "|" + datos.get('numero','')
        bot.send_message(call.message.chat.id,
                         "💳 *" + pais + "*\nActual: `" + actual + "`\n\nNuevo: `metodo|titular|numero`",
                         parse_mode="Markdown")

    elif d == "add_pais":
        set_paso(uid, "new_pais")
        bot.send_message(call.message.chat.id, "💳 Escribe:\n`NombrePais|metodo|titular|numero`",
                         parse_mode="Markdown")

    elif d.startswith("aprob_"):
        rid = int(d[6:])
        cur.execute("SELECT user_id, monto FROM recargas WHERE id=?", (rid,))
        rec = cur.fetchone()
        if rec:
            uid_r, monto = rec
            u = get_user(uid_r)
            nuevo = round(u[2] + monto, 2)
            cur.execute("UPDATE usuarios SET saldo=? WHERE id=?", (nuevo, uid_r))
            cur.execute("UPDATE recargas SET estado='aprobada' WHERE id=?", (rid,))
            cur.execute("INSERT INTO movimientos VALUES (NULL,?,?,?,?)",
                        (uid_r, "recarga", monto, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            bot.send_message(call.message.chat.id,
                             "✅ " + u[1] + " +$" + str(monto) + " = $" + str(nuevo),
                             reply_markup=menu_admin())
            bot.send_message(uid_r,
                             "✅ *Recarga aprobada!*\n+$" + str(monto) + "\n💳 Saldo: $" + str(nuevo),
                             parse_mode="Markdown", reply_markup=menu_cliente())

    elif d.startswith("rech_"):
        rid = int(d[5:])
        cur.execute("SELECT user_id, monto FROM recargas WHERE id=?", (rid,))
        rec = cur.fetchone()
        if rec:
            uid_r, monto = rec
            cur.execute("UPDATE recargas SET estado='rechazada' WHERE id=?", (rid,))
            conn.commit()
            u = get_user(uid_r)
            bot.send_message(call.message.chat.id,
                             "❌ " + u[1] + " $" + str(monto) + " rechazada",
                             reply_markup=menu_admin())
            bot.send_message(uid_r,
                             "❌ *Recarga rechazada*\n$" + str(monto) + "\nContacta al soporte.",
                             parse_mode="Markdown", reply_markup=menu_cliente())

print("✅ BOT FUNCIONANDO")
bot.infinity_polling()
