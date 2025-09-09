from django.shortcuts import render, get_object_or_404, redirect
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
        
        # Get selected sections from session or default to all
        selected_sections = request.session.get('selected_sections', ['heater', 'tank', 'pump'])
        context['selected_sections'] = selected_sections

    if request.method == 'POST':
        job_number = request.POST.get('job_number', '').strip()
        job_name = request.POST.get('job_name', '').strip() or None
        if job_number:
            D365Job.objects.update_or_create(job_number=job_number, defaults={'job_name': job_name})
        
        # Handle selected sections for generate_selected
        if request.POST.get('generate_selected'):
            selected_sections = request.POST.get('selected_sections', '').split(',')
            request.session['selected_sections'] = selected_sections
            context['selected_sections'] = selected_sections

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
                stack_height = to_float('stack_height')
                heater = D365Heater.objects.create(
                    job_number=job_number,
                    dash_number=heater_dash,
                    heater_diameter=hd,
                    heater_height=hh,
                    stack_diameter=sd,
                    stack_height=stack_height,
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
                context['heater_items'] = _format_items(
                    job_number,
                    heater.dash_number or '01',
                    _build_heater_rows(heater, heater.stack_height),
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


@login_required
def generate_selected(request: HttpRequest) -> HttpResponse:
    """Generate items for selected sections only"""
    jobs = D365Job.objects.order_by('-updated_at')[:50]
    selected_sections = request.POST.get('selected_sections', '').split(',')
    
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

    context: dict = {'jobs': jobs, **ref, 'selected_sections': selected_sections}

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

        # Process only selected sections
        if 'heater' in selected_sections and (request.POST.get('heater_submit') == '1' or request.POST.get('generate_selected') == '1'):
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
                stack_height = to_float('stack_height')
                heater = D365Heater.objects.create(
                    job_number=job_number,
                    dash_number=heater_dash,
                    heater_diameter=hd,
                    heater_height=hh,
                    stack_diameter=sd,
                    stack_height=stack_height,
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
                context['heater_items'] = _format_items(
                    job_number, heater_dash or '01', _build_heater_rows(heater, heater.stack_height)
                )
                context['heater_initial'] = heater
                context['heater_dash_value'] = heater_dash or '01'

        if 'tank' in selected_sections and (request.POST.get('tank_submit') == '1' or request.POST.get('generate_selected') == '1'):
            td = to_int('tank_diameter')
            th = to_int('tank_height')
            ti = to_float('tank_inches')
            material = request.POST.get('tank_material')
            tank_type = request.POST.get('tank_type')
            if None not in (td, th, ti) and all([material, tank_type]):
                tank_dash = request.POST.get('tank_dash_number') or None
                tank = D365Tank.objects.create(
                    job_number=job_number,
                    dash_number=tank_dash,
                    tank_diameter=td,
                    tank_height=th,
                    tank_inches=ti,
                    material=material,
                    tank_type=tank_type,
                )
                context['tank_items'] = _format_items(job_number, tank_dash or '01', _build_tank_rows(tank))
                context['tank_initial'] = tank
                context['tank_dash_value'] = tank_dash or '01'

        if 'pump' in selected_sections and (request.POST.get('pump_submit') == '1' or request.POST.get('generate_selected') == '1'):
            pump_type = request.POST.get('pump_type')
            pump_pressure = request.POST.get('pump_pressure')
            system_type = request.POST.get('system_type')
            hp = to_float('hp')
            material = request.POST.get('pump_material')
            sl = to_float('skid_length')
            sw = to_float('skid_width')
            sh = to_float('skid_height')
            if all([pump_type, pump_pressure, system_type, hp, material, sl, sw, sh]):
                pump_dash = request.POST.get('pump_dash_number') or None
                pump = D365Pump.objects.create(
                    job_number=job_number,
                    dash_number=pump_dash,
                    pump_type=pump_type,
                    pump_pressure=pump_pressure,
                    system_type=system_type,
                    hp=hp,
                    material=material,
                    skid_length=sl,
                    skid_width=sw,
                    skid_height=sh,
                )
                context['pump_items'] = _format_items(job_number, pump_dash or '01', _build_pump_rows(pump))
                context['pump_initial'] = pump
                context['pump_dash_value'] = pump_dash or '01'

        context['job_number'] = job_number
        context['job_name'] = job_name

    return render(request, 'd365/generate.html', context)


@login_required
def save_selection(request: HttpRequest) -> JsonResponse:
    """Save selected sections to session"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        selected_sections = data.get('selected_sections', [])
        request.session['selected_sections'] = selected_sections
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def generate_heater(request: HttpRequest) -> HttpResponse:
    """Generate only heater items"""
    return generate_section(request, 'heater')

@login_required
def generate_tank(request: HttpRequest) -> HttpResponse:
    """Generate only tank items"""
    return generate_section(request, 'tank')

@login_required
def generate_pump(request: HttpRequest) -> HttpResponse:
    """Generate only pump items"""
    return generate_section(request, 'pump')

def generate_section(request: HttpRequest, section: str) -> HttpResponse:
    """Helper function to generate items for a specific section"""
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

    context: dict = {'jobs': jobs, **ref, 'current_section': section}

    # Handle GET request - load existing job data
    if request.method == 'GET':
        job_q = request.GET.get('job')
        if job_q:
            job = D365Job.objects.filter(job_number=job_q).first()
            context['job_number'] = job_q
            context['job_name'] = job.job_name if job else ''
            
            if section == 'heater':
                heater = D365Heater.objects.filter(job_number=job_q).order_by('-created_at').first()
                context['heater_initial'] = heater if heater else None
                context['heater_dash_value'] = (heater.dash_number if heater and heater.dash_number else '01')
            elif section == 'tank':
                tank = D365Tank.objects.filter(job_number=job_q).order_by('-created_at').first()
                context['tank_initial'] = tank if tank else None
                context['tank_dash_value'] = (tank.dash_number if tank and tank.dash_number else '01')
            elif section == 'pump':
                pump = D365Pump.objects.filter(job_number=job_q).order_by('-created_at').first()
                context['pump_initial'] = pump if pump else None
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

        # Process only the specific section
        if section == 'heater':
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
                stack_height = to_float('stack_height')
                heater = D365Heater.objects.create(
                    job_number=job_number,
                    dash_number=heater_dash,
                    heater_diameter=hd,
                    heater_height=hh,
                    stack_diameter=sd,
                    stack_height=stack_height,
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
                context['heater_items'] = _format_items(
                    job_number, heater_dash or '01', _build_heater_rows(heater, heater.stack_height)
                )
                context['heater_initial'] = heater
                context['heater_dash_value'] = heater_dash or '01'
            else:
                # If validation failed, preserve form data
                context['heater_initial'] = type('obj', (object,), {
                    'heater_diameter': hd,
                    'heater_height': hh,
                    'stack_diameter': sd,
                    'stack_height': to_float('stack_height'),
                    'flange_inlet': fi,
                    'heater_model': model,
                    'material': material,
                    'gas_train_size': gts,
                    'gas_train_mount': mount,
                    'btu': btu,
                    'hand': hand,
                    'heater_ab': request.POST.get('heater_ab', ''),
                    'heater_single_dual': request.POST.get('heater_single_dual', 'S'),
                    'dash_number': request.POST.get('heater_dash_number', '01')
                })()
                context['heater_dash_value'] = request.POST.get('heater_dash_number', '01')

        elif section == 'tank':
            td = to_int('tank_diameter')
            th = to_int('tank_height')
            ti = to_float('tank_inches')
            material = request.POST.get('tank_material')
            tank_type = request.POST.get('tank_type')
            if None not in (td, th, ti) and all([material, tank_type]):
                tank_dash = request.POST.get('tank_dash_number') or None
                tank = D365Tank.objects.create(
                    job_number=job_number,
                    dash_number=tank_dash,
                    tank_diameter=td,
                    tank_height=th,
                    tank_inches=ti,
                    material=material,
                    tank_type=tank_type,
                )
                context['tank_items'] = _format_items(job_number, tank_dash or '01', _build_tank_rows(tank))
                context['tank_initial'] = tank
                context['tank_dash_value'] = tank_dash or '01'
            else:
                # If validation failed, preserve form data
                context['tank_initial'] = type('obj', (object,), {
                    'tank_diameter': td,
                    'tank_height': th,
                    'tank_inches': ti,
                    'material': material,
                    'tank_type': tank_type,
                    'dash_number': request.POST.get('tank_dash_number', '01')
                })()
                context['tank_dash_value'] = request.POST.get('tank_dash_number', '01')

        elif section == 'pump':
            pump_type = request.POST.get('pump_type')
            pump_pressure = request.POST.get('pump_pressure')
            system_type = request.POST.get('system_type')
            hp = to_float('hp')
            material = request.POST.get('pump_material')
            sl = to_float('skid_length')
            sw = to_float('skid_width')
            sh = to_float('skid_height')
            if all([pump_type, pump_pressure, system_type, hp, material, sl, sw, sh]):
                pump_dash = request.POST.get('pump_dash_number') or None
                pump = D365Pump.objects.create(
                    job_number=job_number,
                    dash_number=pump_dash,
                    pump_type=pump_type,
                    pump_pressure=pump_pressure,
                    system_type=system_type,
                    hp=hp,
                    material=material,
                    skid_length=sl,
                    skid_width=sw,
                    skid_height=sh,
                )
                context['pump_items'] = _format_items(job_number, pump_dash or '01', _build_pump_rows(pump))
                context['pump_initial'] = pump
                context['pump_dash_value'] = pump_dash or '01'
            else:
                # If validation failed, preserve form data
                context['pump_initial'] = type('obj', (object,), {
                    'pump_type': pump_type,
                    'pump_pressure': pump_pressure,
                    'system_type': system_type,
                    'hp': hp,
                    'material': material,
                    'skid_length': sl,
                    'skid_width': sw,
                    'skid_height': sh,
                    'dash_number': request.POST.get('pump_dash_number', '01')
                })()
                context['pump_dash_value'] = request.POST.get('pump_dash_number', '01')

        context['job_number'] = job_number
        context['job_name'] = job_name

    # Always ensure we have selected_sections for the template
    if 'selected_sections' not in context:
        context['selected_sections'] = ['heater', 'tank', 'pump']

    return render(request, f'd365/generate_{section}.html', context)


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
def delete_job(request: HttpRequest, job_id: int) -> HttpResponse:
    job = get_object_or_404(D365Job, id=job_id)
    # Optionally cascade delete related section rows
    D365Heater.objects.filter(job_number=job.job_number).delete()
    D365Tank.objects.filter(job_number=job.job_number).delete()
    D365Pump.objects.filter(job_number=job.job_number).delete()
    job.delete()
    return redirect('d365_home')


@login_required
def print_job(request: HttpRequest, job_number: str) -> HttpResponse:
    job = get_object_or_404(D365Job, job_number=job_number)
    heater = D365Heater.objects.filter(job_number=job_number).order_by('-created_at').first()
    tank = D365Tank.objects.filter(job_number=job_number).order_by('-created_at').first()
    pump = D365Pump.objects.filter(job_number=job_number).order_by('-created_at').first()

    # Get selected sections from query parameter
    selected_sections = request.GET.get('sections', 'heater,tank,pump').split(',')
    
    # Use the same formatting logic as the generator
    heater_items = []
    tank_items = []
    pump_items = []
    
    if 'heater' in selected_sections and heater:
        heater_items = _format_items(job_number, heater.dash_number or '01', _build_heater_rows(heater, heater.stack_height))
    
    if 'tank' in selected_sections and tank:
        tank_items = _format_items(job_number, tank.dash_number or '01', _build_tank_rows(tank))
    
    if 'pump' in selected_sections and pump:
        pump_items = _format_items(job_number, pump.dash_number or '01', _build_pump_rows(pump))

    return render(request, 'd365/print.html', {
        'job': job,
        'heater_items': heater_items,
        'tank_items': tank_items,
        'pump_items': pump_items,
        'selected_sections': selected_sections,
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

    # Use the same formatting logic as the generator
    heater_items = []
    tank_items = []
    pump_items = []
    
    if heater:
        heater_items = _format_items(job_number, heater.dash_number or '01', _build_heater_rows(heater, heater.stack_height))
    
    if tank:
        tank_items = _format_items(job_number, tank.dash_number or '01', _build_tank_rows(tank))
    
    if pump:
        pump_items = _format_items(job_number, pump.dash_number or '01', _build_pump_rows(pump))

    payload = {
        'job': {'id': job.id, 'job_number': job.job_number, 'job_name': job.job_name, 'updated_at': job.updated_at},
        'heater': model_to_dict(heater),
        'tank': model_to_dict(tank),
        'pump': model_to_dict(pump),
        'heater_items': heater_items,
        'tank_items': tank_items,
        'pump_items': pump_items,
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

        # Excel formula: =CONCATENATE($I$2,"-",$I$3) for main items
        if seq == 0:
            item_number = f"{job_number}-{dash}"
        else:
            # Allow special override like '-A' for certain rows (e.g., Tank precut)
            suffix = row.get('override_suffix')
            if suffix:
                item_number = f"{job_number}-{dash}.1-{suffix}"
            else:
                # Excel formula: =CONCATENATE($I$2,"-",$I$3,".1") for sub-items
                item_number = f"{job_number}-{dash}.{seq}"
        
        # Excel formula: =CONCATENATE($I$2,"-",$I$3,"-000") for main items
        # Excel formula: =CONCATENATE($I$2,"-",$I$3,".1","-000") for sub-items
        bom = f"{item_number}-000"
        
        # Template logic: main items (-01) are "FGFAB", sub-items (.1, .2, etc.) are "Sub Assy"
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
    fi = _fmt_dim(heater.flange_inlet)

    rows: list[dict] = []
    
    # Excel formula: =IF(I14=0,CONCATENATE("HEATER, FAB, ",I4,"X",I5,", ",I8,", ",I9),CONCATENATE("HEATER ",I14,", FAB, ",I4,"X",I5,", ",I8,", ",I9))
    if not ab:
        desc0 = f"HEATER, FAB, {d}X{h}, {material}, {model}"
    else:
        desc0 = f"HEATER {ab}, FAB, {d}X{h}, {material}, {model}"
    rows.append({'description': desc0, 'product_type': 'Finished Good'})

    # Excel formula: =IF(I14=0,CONCATENATE("HEATER, WELD, ",I4,"X",I5,", ",I9),CONCATENATE("HEATER ",I14,", WELD, ",I4,"X",I5,", ",I9))
    if not ab:
        desc1 = f"HEATER, WELD, {d}X{h}, {material}"
    else:
        desc1 = f"HEATER {ab}, WELD, {d}X{h}, {material}"
    rows.append({'description': desc1, 'product_type': 'Pegged Supply'})
    
    # Excel formula: =IF(I14=0,CONCATENATE("HEATER, SHELL, ",I4,"X",I5,", ",I9),CONCATENATE("HEATER ",I14,", SHELL, ",I4,"X",I5,", ",I9))
    if not ab:
        desc2 = f"HEATER, SHELL, {d}X{h}, {material}"
    else:
        desc2 = f"HEATER {ab}, SHELL, {d}X{h}, {material}"
    rows.append({'description': desc2, 'product_type': 'Raw Material'})
    
    # Excel formula: =IF(I14=0,CONCATENATE("HEATER, STACK, ",I6,"X",I16,", W/",I7,"FL"),CONCATENATE("HEATER ",I14,", STACK, ",I6,"X",I16,", W/",I7,"FL"))
    if not ab:
        desc3 = f"HEATER, STACK, {sd}X{sh}, W/{fi}FL"
    else:
        desc3 = f"HEATER {ab}, STACK, {sd}X{sh}, W/{fi}FL"
    rows.append({'description': desc3, 'product_type': 'Raw Material'})
    
    # Excel formula: =IF(I14=0,CONCATENATE("GAS TRAIN, ",I10,", ",I11,", ","SIEMENS",", ",I12,"MBTU, ",I13),CONCATENATE("GAS TRAIN, HTR ",I14, ", ",I10,", ",I11,", ","SIEMENS",", ",I12,"MBTU, ",I13))
    if not ab:
        desc4 = f"GAS TRAIN, {gts}, {mount}, SIEMENS, {btu}MBTU, {hand}"
    else:
        desc4 = f"GAS TRAIN, HTR {ab}, {gts}, {mount}, SIEMENS, {btu}MBTU, {hand}"
    rows.append({'description': desc4, 'product_type': 'Pegged Supply'})
    
    # Excel formula: =IF(I15="SINGLE",I17,I18)
    # This should be a proper description, not just the ab value
    if heater.heater_single_dual == 'SINGLE':
        mod_piping_desc = f"HEATER, MOD PIPING, {model}"
    else:
        mod_piping_desc = f"HEATER, MOD PIPING, {model}"
    rows.append({'description': mod_piping_desc, 'product_type': 'Raw Material'})
    
    # Excel formula: =IF(I14=0,CONCATENATE("PRECUT HTR",I4,", ",I6,"STACK, 11GA, ",I9),CONCATENATE("PRECUT HTR",I14,I4,", ",I6,"STACK, 11GA, ",I9))
    if not ab:
        precut_desc = f"PRECUT HTR{d}, {sd}STACK, 11GA, {material}"
    else:
        precut_desc = f"PRECUT HTR{ab}{d}, {sd}STACK, 11GA, {material}"
    rows.append({'description': precut_desc, 'product_type': 'Raw Material', 'override_suffix': 'A'})
    
    return rows


def _build_tank_rows(tank: D365Tank) -> list[dict]:
    d = _fmt_dim(tank.tank_diameter)
    h = _fmt_dim(tank.tank_height)
    material = (tank.material or '').upper()
    ttype = (tank.tank_type or '').upper()
    ti = _fmt_dim(tank.tank_inches)
    
    rows: list[dict] = []
    
    # Excel formula: =CONCATENATE("TANK, ",H4,"X",H5,", ",H7,", ",H6)
    rows.append({'description': f"TANK, {d}X{h}, {ttype}, {material}", 'product_type': 'Finished Good'})
    
    # Excel formula: =CONCATENATE("TANK, SHELL, ",H4,"X",H8,", ",H6)
    rows.append({'description': f"TANK, SHELL, {d}X{ti}, {material}", 'product_type': 'Raw Material'})
    
    # Excel formula: =CONCATENATE("PRECUT TANK",H4,"X",H5,", 11GA, ",H6)
    rows.append({'description': f"PRECUT TANK{d}X{h}, 11GA, {material}", 'product_type': 'Raw Material', 'override_suffix': 'A'})
    
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
    
    # Excel formula: =IF(G4="LP",CONCATENATE("PUMP, ",G3,", ",G5,", ",G6,"HP"),CONCATENATE("PUMP, ",G3,", ",G4,", ",G5,", ",G6,"HP"))
    if ppress == "LP":
        pump_desc = f"PUMP, {ptype}, {stype}, {hp}HP"
    else:
        pump_desc = f"PUMP, {ptype}, {ppress}, {stype}, {hp}HP"
    rows.append({'description': pump_desc, 'product_type': 'Finished Good'})
    
    # Excel formula: =CONCATENATE("PUMP SKID, ",G3,", ",G8,"X",G9,"X",G10,", ",G7)
    rows.append({'description': f"PUMP SKID, {ptype}, {sl}X{sw}X{sh}, {material}", 'product_type': 'Raw Material'})
    
    # Excel formula: =IF(G3="SIMPLEX",CONCATENATE("PRECUT, ",G3," PUMP SKID",","," 11GA"),CONCATENATE("PRECUT, ",G3," PUMP SKID",","," 3/16PL"))
    if ptype == "SIMPLEX":
        precut_desc = f"PRECUT, {ptype} PUMP SKID, 11GA"
    else:
        precut_desc = f"PRECUT, {ptype} PUMP SKID, 3/16PL"
    rows.append({'description': precut_desc, 'product_type': 'Raw Material', 'override_suffix': 'A'})
    
    return rows

# Create your views here.
