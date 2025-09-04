from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import (
    D365Job, D365Heater, D365Tank, D365Pump,
    HeaterMaterial, HeaterDiameter, HeaterHeight, StackDiameter, StackHeight,
    FlangeInlet, HeaterModelRef, GasTrainSize, GasTrainMount, BTURating,
    HeaterHandRef, HeaterABRef,
    TankMaterial, TankDiameter, TankHeight, TankHeightInches, TankType,
    PumpMaterial, PumpTypeRef, PumpPressure, SystemType, Horsepower,
)
from .excel import read_workbook_outputs
from pathlib import Path


@login_required
def d365_home(request: HttpRequest) -> HttpResponse:
    jobs = D365Job.objects.order_by('-updated_at')[:50]
    return render(request, 'd365/index.html', {
        'jobs': jobs,
    })


@login_required
@require_http_methods(["GET", "POST"])
def generate_all(request: HttpRequest) -> HttpResponse:
    jobs = D365Job.objects.order_by('-updated_at')[:50]

    ref = {
        'heater_materials': HeaterMaterial.objects.all(),
        'heater_diameters': HeaterDiameter.objects.all(),
        'heater_heights': HeaterHeight.objects.all(),
        'stack_diameters': StackDiameter.objects.all(),
        'stack_heights': StackHeight.objects.all(),
        'flange_inlets': FlangeInlet.objects.all(),
        'heater_models': HeaterModelRef.objects.all(),
        'gas_train_sizes': GasTrainSize.objects.all(),
        'gas_train_mounts': GasTrainMount.objects.all(),
        'btu_ratings': BTURating.objects.all(),
        'heater_hands': HeaterHandRef.objects.all(),
        'heater_ab_list': HeaterABRef.objects.all(),

        'tank_materials': TankMaterial.objects.all(),
        'tank_diameters': TankDiameter.objects.all(),
        'tank_heights': TankHeight.objects.all(),
        'tank_types': TankType.objects.all(),

        'pump_materials': PumpMaterial.objects.all(),
        'pump_types': PumpTypeRef.objects.all(),
        'pump_pressures': PumpPressure.objects.all(),
        'system_types': SystemType.objects.all(),
        'horsepower': Horsepower.objects.all(),
    }

    context: dict = {'jobs': jobs, **ref}

    # Prefill from query param (?job=JOB)
    if request.method == 'GET':
        job_q = request.GET.get('job')
        if job_q:
            job = D365Job.objects.filter(job_number=job_q).first()
            context['job_number'] = job_q
            context['job_name'] = job.job_name if job else ''
            heater = D365Heater.objects.filter(job_number=job_q).order_by('-created_at').first()
            tank = D365Tank.objects.filter(job_number=job_q).order_by('-created_at').first()
            pump = D365Pump.objects.filter(job_number=job_q).order_by('-created_at').first()
            context['heater_initial'] = heater if heater else None
            context['tank_initial'] = tank if tank else None
            context['pump_initial'] = pump if pump else None
            context['heater_dash_value'] = (heater.dash_number if heater and heater.dash_number else '01')
            context['tank_dash_value'] = (tank.dash_number if tank and tank.dash_number else '01')
            context['pump_dash_value'] = (pump.dash_number if pump and pump.dash_number else '01')

    if request.method == 'POST':
        job_number = request.POST.get('job_number', '').strip()
        job_name = request.POST.get('job_name', '').strip() or None
        if job_number:
            D365Job.objects.update_or_create(job_number=job_number, defaults={'job_name': job_name})

        def to_int(name: str):
            val = request.POST.get(name)
            try:
                return int(val) if val not in (None, '') else None
            except (TypeError, ValueError):
                return None

        def to_float(name: str):
            val = request.POST.get(name)
            try:
                return float(val) if val not in (None, '') else None
            except (TypeError, ValueError):
                return None

        # Heater
        if request.POST.get('heater_submit') == '1' or request.POST.get('generate_all') == '1':
            hd = to_int('heater_diameter')
            hh = to_float('heater_height')
            sd = to_int('stack_diameter')
            fi = to_float('flange_inlet')
            gts = to_float('gas_train_size')
            btu = to_float('btu')
            model = request.POST.get('heater_model')
            material = request.POST.get('heater_material')
            mount = request.POST.get('gas_train_mount')
            hand = request.POST.get('heater_hand')
            if None not in (hd, hh, sd, fi, gts, btu) and all([model, material, mount, hand]):
                heater_dash = request.POST.get('heater_dash_number') or None
                heater = D365Heater.objects.create(
                    job_number=job_number,
                    dash_number=heater_dash,
                    heater_diameter=hd,
                    heater_height=hh,
                    stack_diameter=sd,
                    flange_inlet=fi,
                    heater_model=model,
                    material=material,
                    gas_train_size=gts,
                    gas_train_mount=mount,
                    btu=btu,
                    hand=hand,
                    heater_ab=(request.POST.get('heater_ab') or ''),
                    heater_single_dual=(request.POST.get('heater_single_dual') or 'S'),
                )
                stack_height = to_float('stack_height')
                context['heater_items'] = _format_items(
                    job_number,
                    heater.dash_number or '01',
                    _build_heater_rows(heater, stack_height),
                )
                context['heater_initial'] = heater
                context['heater_dash_value'] = heater_dash or (heater.dash_number or '01')

        # Tank
        if request.POST.get('tank_submit') == '1' or request.POST.get('generate_all') == '1':
            td = to_int('tank_diameter')
            th = to_int('tank_height')
            material = request.POST.get('tank_material')
            ttype = request.POST.get('tank_type')
            if None not in (td, th) and all([material, ttype]):
                ti = TankHeightInches.objects.filter(height_ft=th).first()
                tank_inches = float(ti.inches) if ti else 0.0
                tank_dash = request.POST.get('tank_dash_number') or None
                tank = D365Tank.objects.create(
                    job_number=job_number,
                    dash_number=tank_dash,
                    tank_diameter=td,
                    tank_height=th,
                    tank_inches=tank_inches,
                    material=material,
                    tank_type=ttype,
                )
                context['tank_items'] = _format_items(
                    job_number,
                    tank.dash_number or '01',
                    _build_tank_rows(tank),
                )
                context['tank_initial'] = tank
                context['tank_dash_value'] = tank_dash or (tank.dash_number or '01')

        # Pump
        if request.POST.get('pump_submit') == '1' or request.POST.get('generate_all') == '1':
            ptype = request.POST.get('pump_type')
            ppress = request.POST.get('pump_pressure')
            stype = request.POST.get('system_type')
            hp = to_float('hp')
            material = request.POST.get('pump_material')
            sl = to_float('skid_length')
            sw = to_float('skid_width')
            sh = to_float('skid_height')
            if None not in (hp, sl, sw, sh) and all([ptype, ppress, stype, material]):
                pump_dash = request.POST.get('pump_dash_number') or None
                pump = D365Pump.objects.create(
                    job_number=job_number,
                    dash_number=pump_dash,
                    pump_type=ptype,
                    pump_pressure=ppress,
                    system_type=stype,
                    hp=hp,
                    material=material,
                    skid_length=sl,
                    skid_width=sw,
                    skid_height=sh,
                )
                context['pump_items'] = _format_items(
                    job_number,
                    pump.dash_number or '01',
                    _build_pump_rows(pump),
                )
                context['pump_initial'] = pump
                context['pump_dash_value'] = pump_dash or (pump.dash_number or '01')

        context['job_number'] = job_number
        context['job_name'] = job_name

    return render(request, 'd365/generate.html', context)


@require_http_methods(["POST"])  # relaxed auth per spec; can add login_required later
def save_job(request: HttpRequest) -> JsonResponse:
    job_number = request.POST.get('job_number') or (request.content_type == 'application/json' and (request.json() if hasattr(request, 'json') else None))
    # Simple, robust extraction supporting form or JSON
    if isinstance(job_number, dict):
        payload = job_number
        job_number = payload.get('job_number')
        job_name = payload.get('job_name')
    else:
        job_name = request.POST.get('job_name')
    if not job_number:
        return JsonResponse({'success': False, 'message': 'job_number is required'}, status=400)
    job, created = D365Job.objects.update_or_create(
        job_number=job_number,
        defaults={
            'job_name': job_name,
        }
    )
    return JsonResponse({'success': True, 'message': 'Saved' if created else 'Updated', 'job_id': job.id})


@login_required
def load_job_by_id(request: HttpRequest, job_id: int) -> JsonResponse:
    job = get_object_or_404(D365Job, id=job_id)
    return _job_payload(job)


@login_required
def load_job_by_number(request: HttpRequest, job_number: str) -> JsonResponse:
    job = get_object_or_404(D365Job, job_number=job_number)
    return _job_payload(job)


@login_required
def jobs_list(request: HttpRequest) -> JsonResponse:
    jobs = list(D365Job.objects.order_by('-updated_at').values('id', 'job_number', 'job_name', 'updated_at'))
    return JsonResponse(jobs, safe=False)


@login_required
@require_http_methods(["POST"])
def delete_job(request: HttpRequest, job_id: int) -> JsonResponse:
    job = get_object_or_404(D365Job, id=job_id)
    # Optionally cascade delete related section rows
    D365Heater.objects.filter(job_number=job.job_number).delete()
    D365Tank.objects.filter(job_number=job.job_number).delete()
    D365Pump.objects.filter(job_number=job.job_number).delete()
    job.delete()
    return JsonResponse({'success': True})


@login_required
def print_job(request: HttpRequest, job_number: str) -> HttpResponse:
    job = get_object_or_404(D365Job, job_number=job_number)
    heater = D365Heater.objects.filter(job_number=job_number).order_by('-created_at').first()
    tank = D365Tank.objects.filter(job_number=job_number).order_by('-created_at').first()
    pump = D365Pump.objects.filter(job_number=job_number).order_by('-created_at').first()

    heater_items = heater.generate_items() if heater else []
    tank_items = tank.generate_items() if tank else []
    pump_items = pump.generate_items() if pump else []

    return render(request, 'd365/print.html', {
        'job': job,
        'heater_items': heater_items,
        'tank_items': tank_items,
        'pump_items': pump_items,
    })


def _job_payload(job: D365Job) -> JsonResponse:
    job_number = job.job_number
    heater = D365Heater.objects.filter(job_number=job_number).order_by('-created_at').first()
    tank = D365Tank.objects.filter(job_number=job_number).order_by('-created_at').first()
    pump = D365Pump.objects.filter(job_number=job_number).order_by('-created_at').first()

    def model_to_dict(instance):
        if not instance:
            return None
        data = {f.name: getattr(instance, f.name) for f in instance._meta.fields}
        return data

    payload = {
        'job': {'id': job.id, 'job_number': job.job_number, 'job_name': job.job_name, 'updated_at': job.updated_at},
        'heater': model_to_dict(heater),
        'tank': model_to_dict(tank),
        'pump': model_to_dict(pump),
        'heater_items': heater.generate_items() if heater else [],
        'tank_items': tank.generate_items() if tank else [],
        'pump_items': pump.generate_items() if pump else [],
    }
    return JsonResponse(payload)


@login_required
def excel_preview(request: HttpRequest) -> HttpResponse:
    # Path to workbook in project root as per user-provided file
    workbook_path = Path('d265_import.xlsx')
    outputs = {}
    if workbook_path.exists():
        outputs = read_workbook_outputs(workbook_path)
    return render(request, 'd365/excel_preview.html', {
        'has_file': workbook_path.exists(),
        'outputs': outputs,
    })


def _format_items(job_number: str, dash: str, items: list[dict]) -> list[dict]:
    formatted: list[dict] = []
    for seq, row in enumerate(items):
        product_type = row.get('product_type', '')
        type_map = {
            'Finished Good': 'Item',
            'Subassembly': 'Sub Assy',
            'Raw Material': 'Phantom',
            'Purchased': 'Pegged Supply',
            'Sub Assy': 'Sub Assy',
            'Item': 'Item',
            'Phantom': 'Phantom',
        }
        pt = type_map.get(product_type, product_type)

        if seq == 0:
            item_number = f"{job_number}-{dash}"
        else:
            # Allow special override like '-A' for certain rows (e.g., Tank precut)
            suffix = row.get('override_suffix')
            if suffix:
                item_number = f"{job_number}-{dash}-{suffix}"
            else:
                item_number = f"{job_number}-{dash}.{seq}"
        bom = f"{item_number}-000"
        template = "FGFAB" if seq == 0 else "Sub Assy"

        formatted.append({
            'item_number': item_number,
            'description': row.get('description', ''),
            'bom': bom,
            'template': template,
            'product_type': pt or 'Item',
        })
    return formatted


def _fmt_dim(value: float | int) -> str:
    # Trim .0
    try:
        iv = int(value)
        if float(value) == float(iv):
            return f"{iv}"
        return f"{value}"
    except Exception:
        return str(value)


def _build_heater_rows(heater: D365Heater, stack_height: float | None) -> list[dict]:
    d = _fmt_dim(heater.heater_diameter)
    h = _fmt_dim(heater.heater_height)
    sd = _fmt_dim(heater.stack_diameter)
    sh = _fmt_dim(stack_height if stack_height is not None else heater.heater_height)
    model = (heater.heater_model or '').upper()
    material = (heater.material or '').upper()
    hand = (heater.hand or '').upper()
    mount = (heater.gas_train_mount or '').upper()
    gts = _fmt_dim(heater.gas_train_size)
    btu = _fmt_dim(heater.btu)
    ab = (heater.heater_ab or '').strip().upper()

    rows: list[dict] = []
    # Main assembly description per Excel rule
    if not ab:
        desc0 = f"HEATER, FAB, {d}X{h}, {model}, {material}"
    else:
        desc0 = f"HEATER {ab}, FAB, {d}X{h}, {model}, {material}"
    rows.append({'description': desc0, 'product_type': 'Item'})

    # .1 Weld assembly (always Pegged Supply per spec)
    rows.append({'description': f"HEATER, WELD, {d}X{h}, {material}", 'product_type': 'Pegged Supply'})
    # .2 Shell
    rows.append({'description': f"HEATER, SHELL, {d}X{h}, {material}", 'product_type': 'Sub Assy'})
    # .3 Stack
    rows.append({'description': f"HEATER, STACK, {sd}X{sh}, W/2FL", 'product_type': 'Sub Assy'})
    # .4 Gas train
    rows.append({'description': f"GAS TRAIN, {gts}, {mount}, SIEMENS, {btu}MBTU, {hand}", 'product_type': 'Pegged Supply'})
    # .5 Mod piping
    rows.append({'description': f"HEATER, MOD PIPING, {model}", 'product_type': 'Sub Assy'})
    # Precut heater same numbering rule (-A)
    rows.append({'description': f"PRECUT HTR, {material}", 'product_type': 'Phantom', 'override_suffix': 'A'})
    return rows


def _build_tank_rows(tank: D365Tank) -> list[dict]:
    d = _fmt_dim(tank.tank_diameter)
    h = _fmt_dim(tank.tank_height)
    material = (tank.material or '').upper()
    ttype = (tank.tank_type or '').upper()
    rows: list[dict] = []
    # seq 0 main
    rows.append({'description': f"TANK, FAB, {d}X{h}, {material}, {ttype}", 'product_type': 'Item'})
    # seq 1 shell
    rows.append({'description': f"TANK, SHELL, {d}X{h}, {material}", 'product_type': 'Sub Assy'})
    # seq 2 precut uses -A numbering in Item Number per Excel; implement via override after formatting
    rows.append({'description': f"TANK, PRECUT, {material}", 'product_type': 'Phantom', 'override_suffix': 'A'})
    return rows


def _build_pump_rows(pump: D365Pump) -> list[dict]:
    ptype = (pump.pump_type or '').upper()
    ppress = (pump.pump_pressure or '').upper()
    stype = (pump.system_type or '').upper()
    hp = _fmt_dim(pump.hp)
    material = (pump.material or '').upper()
    sl = _fmt_dim(pump.skid_length)
    sw = _fmt_dim(pump.skid_width)
    sh = _fmt_dim(pump.skid_height)
    rows: list[dict] = []
    rows.append({'description': f"PUMP, {ptype}, {ppress}, {stype}, {hp}HP, {material}", 'product_type': 'Item'})
    rows.append({'description': f"SKID, {sl}X{sw}X{sh}", 'product_type': 'Sub Assy'})
    # Precut pump uses -A suffix in item number
    rows.append({'description': f"PUMP, PRECUT, {material}", 'product_type': 'Phantom', 'override_suffix': 'A'})
    return rows

# Create your views here.
