import os
from datetime import date, datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, extract

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "jl-eletrica-dev")
default_db = "sqlite:///" + os.path.join(app.root_path, "data", "jl_eletrica.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_db)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, index=True)
    document = db.Column(db.String(40), default="")
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.String(180), default="")
    city = db.Column(db.String(80), default="")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", backref="vehicles")
    plate = db.Column(db.String(12), default="", index=True)
    brand = db.Column(db.String(80), default="")
    model = db.Column(db.String(100), default="")
    year = db.Column(db.String(20), default="")
    color = db.Column(db.String(40), default="")
    notes = db.Column(db.Text, default="")
    @property
    def display_name(self):
        base = " ".join(x for x in [self.brand, self.model, self.year] if x)
        return f"{base} - {self.plate}".strip(" -")

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", backref="locations")
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(180), default="")
    reference = db.Column(db.String(120), default="")
    notes = db.Column(db.Text, default="")

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))
    client = db.relationship("Client")
    location = db.relationship("Location")
    vehicle = db.relationship("Vehicle")
    service_type = db.Column(db.String(80), default="Elétrica automotiva")
    mileage = db.Column(db.String(30), default="")
    date = db.Column(db.Date, default=date.today, index=True)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(40), default="Aberta", index=True)
    description = db.Column(db.Text, default="")
    payment_method = db.Column(db.String(80), default="")
    notes = db.Column(db.Text, default="")
    paid = db.Column(db.Boolean, default=False)
    total = db.Column(db.Numeric(12,2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("WorkOrderItem", cascade="all,delete-orphan", backref="order", lazy=True)

class WorkOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("work_order.id"), nullable=False)
    description = db.Column(db.String(240), nullable=False)
    qty = db.Column(db.Numeric(10,2), default=1)
    unit_price = db.Column(db.Numeric(12,2), default=0)
    @property
    def total(self): return Decimal(self.qty or 0) * Decimal(self.unit_price or 0)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))
    client = db.relationship("Client")
    location = db.relationship("Location")
    vehicle = db.relationship("Vehicle")
    service_type = db.Column(db.String(80), default="Elétrica automotiva")
    mileage = db.Column(db.String(30), default="")
    date = db.Column(db.Date, default=date.today, index=True)
    status = db.Column(db.String(40), default="Pendente", index=True)
    description = db.Column(db.Text, default="")
    payment_method = db.Column(db.String(80), default="")
    notes = db.Column(db.Text, default="")
    total = db.Column(db.Numeric(12,2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("QuoteItem", cascade="all,delete-orphan", backref="quote", lazy=True)

class QuoteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("quote.id"), nullable=False)
    description = db.Column(db.String(240), nullable=False)
    qty = db.Column(db.Numeric(10,2), default=1)
    unit_price = db.Column(db.Numeric(12,2), default=0)
    @property
    def total(self): return Decimal(self.qty or 0) * Decimal(self.unit_price or 0)

def brl(v):
    v = float(v or 0)
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def status_class(s):
    s=(s or "").lower()
    if s in ("concluída","concluida","aprovado","pago"): return "green"
    if s in ("cancelada","cancelado","recusado"): return "red"
    if s in ("em andamento","pendente","aguardando"): return "yellow"
    return "gray"

app.jinja_env.globals.update(brl=brl,status_class=status_class)

def to_date(value):
    try: return datetime.strptime(value, "%Y-%m-%d").date() if value else None
    except: return None

def parse_items():
    descs = request.form.getlist("item_desc[]")
    qtys = request.form.getlist("item_qty[]")
    prices = request.form.getlist("item_price[]")
    items=[]; total=Decimal("0")
    for d,q,p in zip(descs,qtys,prices):
        if not d.strip(): continue
        try: qd=Decimal(q or "0"); pd=Decimal(p or "0")
        except: qd=Decimal("0"); pd=Decimal("0")
        items.append((d.strip(),qd,pd)); total += qd*pd
    return items,total

@app.route("/")
def dashboard():
    now=date.today()
    month_orders=WorkOrder.query.filter(extract("month",WorkOrder.date)==now.month, extract("year",WorkOrder.date)==now.year).all()
    month_quotes=Quote.query.filter(extract("month",Quote.date)==now.month, extract("year",Quote.date)==now.year).all()
    return render_template("dashboard.html", vehicle_count=Vehicle.query.count(),
        receita_mes=sum(float(x.total or 0) for x in month_orders if x.paid),
        os_mes=len(month_orders), os_abertas=sum(1 for x in month_orders if x.status!="Concluída"),
        orc_mes=len(month_quotes), orc_aprovados=sum(1 for x in month_quotes if x.status=="Aprovado"),
        a_receber=sum(float(x.total or 0) for x in WorkOrder.query.filter_by(paid=False).all()),
        ultimas_os=WorkOrder.query.order_by(WorkOrder.id.desc()).limit(6).all(),
        ultimos_orc=Quote.query.order_by(Quote.id.desc()).limit(6).all())

@app.route("/clientes")
def clients():
    q=request.args.get("q","").strip()
    query=Client.query
    if q:
        like=f"%{q}%"
        query=query.filter(or_(Client.name.ilike(like),Client.phone.ilike(like),Client.document.ilike(like),Client.city.ilike(like)))
    data=query.order_by(Client.name).all()
    rows=[{"cells":[c.name,c.phone or "-",c.document or "-",c.city or "-"],"edit_url":f"/clientes/{c.id}/editar","delete_url":f"/clientes/{c.id}/excluir","open_url":None} for c in data]
    return render_template("list.html",title="Clientes",heading="Clientes",subtitle="Pesquise por nome, telefone, CPF/CNPJ ou cidade.",q=q,new_url="/clientes/novo",headers=["Nome","Telefone","CPF/CNPJ","Cidade"],rows=rows,search_placeholder="Buscar cliente...")

@app.route("/clientes/novo", methods=["GET","POST"])
@app.route("/clientes/<int:id>/editar", methods=["GET","POST"])
def client_form(id=None):
    c=Client.query.get_or_404(id) if id else None
    if request.method=="POST":
        if not c: c=Client()
        for f in ["name","document","phone","email","address","city","notes"]: setattr(c,f,request.form.get(f,"").strip())
        db.session.add(c); db.session.commit(); flash("Cliente salvo com sucesso."); return redirect("/clientes")
    return render_template("client_form.html",client=c)

@app.post("/clientes/<int:id>/excluir")
def client_delete(id):
    c=Client.query.get_or_404(id)
    if c.locations or WorkOrder.query.filter_by(client_id=id).first() or Quote.query.filter_by(client_id=id).first():
        flash("Este cliente possui locais, OS ou orçamentos vinculados. Exclua os registros vinculados primeiro.")
    else:
        db.session.delete(c); db.session.commit(); flash("Cliente excluído.")
    return redirect("/clientes")


@app.route("/veiculos")
def vehicles():
    q=request.args.get("q","").strip()
    query=Vehicle.query.join(Client)
    if q:
        like=f"%{q}%"
        query=query.filter(or_(Vehicle.plate.ilike(like),Vehicle.brand.ilike(like),Vehicle.model.ilike(like),Vehicle.year.ilike(like),Client.name.ilike(like)))
    data=query.order_by(Vehicle.id.desc()).all()
    rows=[{"cells":[x.plate or "-",f"{x.brand} {x.model}".strip() or "-",x.year or "-",x.client.name],
           "edit_url":f"/veiculos/{x.id}/editar","delete_url":f"/veiculos/{x.id}/excluir","open_url":None} for x in data]
    return render_template("list.html",title="Veículos",heading="Veículos",subtitle="Cadastre os veículos dos clientes para usar nas OS e orçamentos.",q=q,new_url="/veiculos/novo",headers=["Placa","Veículo","Ano","Cliente"],rows=rows,search_placeholder="Buscar placa, modelo ou cliente...")

@app.route("/veiculos/novo", methods=["GET","POST"])
@app.route("/veiculos/<int:id>/editar", methods=["GET","POST"])
def vehicle_form(id=None):
    x=Vehicle.query.get_or_404(id) if id else None
    if request.method=="POST":
        if not x: x=Vehicle()
        x.client_id=int(request.form["client_id"])
        x.plate=request.form.get("plate","").strip().upper()
        x.brand=request.form.get("brand","").strip()
        x.model=request.form.get("model","").strip()
        x.year=request.form.get("year","").strip()
        x.color=request.form.get("color","").strip()
        x.notes=request.form.get("notes","").strip()
        db.session.add(x); db.session.commit(); flash("Veículo salvo com sucesso."); return redirect("/veiculos")
    return render_template("vehicle_form.html",vehicle=x,clients=Client.query.order_by(Client.name).all())

@app.post("/veiculos/<int:id>/excluir")
def vehicle_delete(id):
    x=Vehicle.query.get_or_404(id)
    if WorkOrder.query.filter_by(vehicle_id=id).first() or Quote.query.filter_by(vehicle_id=id).first():
        flash("Este veículo possui OS ou orçamento vinculado. Altere o vínculo antes de excluir.")
    else:
        db.session.delete(x); db.session.commit(); flash("Veículo excluído.")
    return redirect("/veiculos")

@app.route("/locais")
def locations():
    q=request.args.get("q","").strip(); query=Location.query.join(Client)
    if q:
        like=f"%{q}%"; query=query.filter(or_(Location.name.ilike(like),Location.address.ilike(like),Location.reference.ilike(like),Client.name.ilike(like)))
    data=query.order_by(Location.id.desc()).all()
    rows=[{"cells":[x.name,x.client.name,x.address or "-",x.reference or "-"],"edit_url":f"/locais/{x.id}/editar","delete_url":f"/locais/{x.id}/excluir","open_url":None} for x in data]
    return render_template("list.html",title="Locais / Obras",heading="Locais / Obras",subtitle="Cadastre residências, lojas, quadros, obras e instalações.",q=q,new_url="/locais/novo",headers=["Local","Cliente","Endereço","Referência"],rows=rows,search_placeholder="Buscar local, endereço ou cliente...")

@app.route("/locais/novo", methods=["GET","POST"])
@app.route("/locais/<int:id>/editar", methods=["GET","POST"])
def location_form(id=None):
    x=Location.query.get_or_404(id) if id else None
    if request.method=="POST":
        if not x: x=Location()
        x.client_id=int(request.form["client_id"]); x.name=request.form["name"].strip()
        x.address=request.form.get("address","").strip(); x.reference=request.form.get("reference","").strip(); x.notes=request.form.get("notes","").strip()
        db.session.add(x); db.session.commit(); flash("Local salvo com sucesso."); return redirect("/locais")
    return render_template("location_form.html",location=x,clients=Client.query.order_by(Client.name).all())

@app.post("/locais/<int:id>/excluir")
def location_delete(id):
    x=Location.query.get_or_404(id)
    if WorkOrder.query.filter_by(location_id=id).first() or Quote.query.filter_by(location_id=id).first():
        flash("Este local possui OS ou orçamento vinculado. Exclua ou altere o vínculo primeiro.")
    else:
        db.session.delete(x); db.session.commit(); flash("Local excluído.")
    return redirect("/locais")

def job_list(model, kind):
    q=request.args.get("q","").strip()
    query=model.query.join(Client).outerjoin(Vehicle, model.vehicle_id==Vehicle.id)
    if q:
        like=f"%{q}%"
        clauses=[Client.name.ilike(like),model.status.ilike(like),model.description.ilike(like),Vehicle.plate.ilike(like),Vehicle.model.ilike(like),model.service_type.ilike(like)]
        if q.isdigit(): clauses.append(model.id==int(q))
        query=query.filter(or_(*clauses))
    data=query.order_by(model.id.desc()).all()
    rows=[]
    for x in data:
        payment = ("<span class='badge green'>Pago</span>" if x.paid else "<span class='badge yellow'>Pendente</span>") if kind=="os" else ""
        rows.append({"cells":[f"<strong>#{x.id:04d}</strong>",x.date.strftime("%d/%m/%Y"),x.client.name,f"<span class='badge {status_class(x.status)}'>{x.status}</span>",payment,brl(x.total)],
                     "open_url":f"/{kind if kind=='os' else 'orcamentos'}/{x.id}",
                     "edit_url":f"/{kind if kind=='os' else 'orcamentos'}/{x.id}/editar",
                     "delete_url":f"/{kind if kind=='os' else 'orcamentos'}/{x.id}/excluir"})
    title="Ordens de Serviço" if kind=="os" else "Orçamentos"
    return render_template("list.html",title=title,heading=title,subtitle="Pesquise por número, cliente, status ou descrição.",q=q,new_url=f"/{kind if kind=='os' else 'orcamentos'}/novo",
                           headers=["Nº","Data","Cliente","Status","Pagamento","Total"],rows=rows,search_placeholder="Buscar por número, cliente, status...")

@app.route("/os")
def orders(): return job_list(WorkOrder,"os")

@app.route("/orcamentos")
def quotes(): return job_list(Quote,"orcamento")

def save_job(record, kind):
    record.client_id=int(request.form["client_id"])
    record.location_id=int(request.form["location_id"]) if request.form.get("location_id") else None
    record.vehicle_id=int(request.form["vehicle_id"]) if request.form.get("vehicle_id") else None
    record.service_type=request.form.get("service_type","Elétrica automotiva").strip()
    record.mileage=request.form.get("mileage","").strip()
    record.status=request.form.get("status")
    record.date=to_date(request.form.get("date")) or date.today()
    if kind=="os": record.due_date=to_date(request.form.get("due_date"))
    record.description=request.form.get("description","").strip()
    record.payment_method=request.form.get("payment_method","").strip()
    record.notes=request.form.get("notes","").strip()
    items,total=parse_items(); record.total=total
    record.items.clear()
    db.session.flush()
    Item=WorkOrderItem if kind=="os" else QuoteItem
    for d,q,p in items: record.items.append(Item(description=d,qty=q,unit_price=p))
    db.session.add(record); db.session.commit()

@app.route("/os/novo",methods=["GET","POST"])
@app.route("/os/<int:id>/editar",methods=["GET","POST"])
def order_form(id=None):
    x=WorkOrder.query.get_or_404(id) if id else None
    if request.method=="POST":
        if not x: x=WorkOrder()
        save_job(x,"os"); flash("Ordem de serviço salva."); return redirect(f"/os/{x.id}")
    return render_template("job_form.html",kind="os",record=x,clients=Client.query.order_by(Client.name).all(),locations=Location.query.order_by(Location.name).all(),vehicles=Vehicle.query.order_by(Vehicle.plate).all(),statuses=["Aberta","Em andamento","Aguardando","Concluída","Cancelada"],today=date.today().isoformat())

@app.route("/orcamentos/novo",methods=["GET","POST"])
@app.route("/orcamentos/<int:id>/editar",methods=["GET","POST"])
def quote_form(id=None):
    x=Quote.query.get_or_404(id) if id else None
    if request.method=="POST":
        if not x: x=Quote()
        save_job(x,"orc"); flash("Orçamento salvo."); return redirect(f"/orcamentos/{x.id}")
    return render_template("job_form.html",kind="orc",record=x,clients=Client.query.order_by(Client.name).all(),locations=Location.query.order_by(Location.name).all(),vehicles=Vehicle.query.order_by(Vehicle.plate).all(),statuses=["Pendente","Aprovado","Recusado","Cancelado"],today=date.today().isoformat())

@app.route("/os/<int:id>")
def order_view(id): return render_template("job_view.html",record=WorkOrder.query.get_or_404(id),kind="os")

@app.route("/orcamentos/<int:id>")
def quote_view(id): return render_template("job_view.html",record=Quote.query.get_or_404(id),kind="orc")

@app.post("/os/<int:id>/toggle-pago")
def order_toggle_paid(id):
    x=WorkOrder.query.get_or_404(id); x.paid=not x.paid; db.session.commit(); flash("Pagamento atualizado."); return redirect(f"/os/{id}")

@app.post("/orcamentos/<int:id>/aprovar")
def quote_approve(id):
    x=Quote.query.get_or_404(id); x.status="Aprovado"; db.session.commit(); flash("Orçamento aprovado."); return redirect(f"/orcamentos/{id}")

@app.post("/orcamentos/<int:id>/converter")
def quote_convert(id):
    q=Quote.query.get_or_404(id)
    o=WorkOrder(client_id=q.client_id,location_id=q.location_id,vehicle_id=q.vehicle_id,service_type=q.service_type,mileage=q.mileage,date=date.today(),status="Aberta",description=q.description,payment_method=q.payment_method,notes=f"Convertido do orçamento #{q.id:04d}. {q.notes}".strip(),total=q.total)
    for i in q.items: o.items.append(WorkOrderItem(description=i.description,qty=i.qty,unit_price=i.unit_price))
    q.status="Aprovado"; db.session.add(o); db.session.commit(); flash(f"Orçamento convertido na OS #{o.id:04d}."); return redirect(f"/os/{o.id}")

@app.post("/os/<int:id>/excluir")
def order_delete(id):
    x=WorkOrder.query.get_or_404(id); db.session.delete(x); db.session.commit(); flash("OS excluída."); return redirect("/os")

@app.post("/orcamentos/<int:id>/excluir")
def quote_delete(id):
    x=Quote.query.get_or_404(id); db.session.delete(x); db.session.commit(); flash("Orçamento excluído."); return redirect("/orcamentos")

@app.route("/financeiro")
def finance():
    mes=request.args.get("mes") or date.today().strftime("%Y-%m")
    try: year,month=map(int,mes.split("-"))
    except: year,month=date.today().year,date.today().month
    orders=WorkOrder.query.filter(extract("year",WorkOrder.date)==year,extract("month",WorkOrder.date)==month).order_by(WorkOrder.date.desc()).all()
    recebido=sum(float(x.total or 0) for x in orders if x.paid); receber=sum(float(x.total or 0) for x in orders if not x.paid); total=recebido+receber
    return render_template("finance.html",mes=mes,orders=orders,recebido=recebido,receber=receber,total=total,ticket=(total/len(orders) if orders else 0))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8000,debug=True)
