% DIN / KTW Wissensbasis für Typ A, B, C und Synonyme

% Allgemeine Fahrzeugdaten
vehicle(ktw_a).  % Krankentransportwagen Typ A
vehicle(ktw_b).  % Krankentransportwagen Typ B
vehicle(ktw_c).  % Krankentransportwagen Typ C
vehicle(rtw).    % Rettungswagen
vehicle(notfall_ktw).

% Normen
norm(din_en_1789).
norm(din_en_1789_teil1).
norm(din_en_1789_teil2).
norm(din_en_1846).

% Typen
ktw_type(typ_a).
ktw_type(typ_b).
ktw_type(typ_c).
ktw_type(rettungswagen).

% Synonyme und alternative Bezeichnungen
synonym(rtw, rettungswagen).
synonym(ktw_c, typ_c).
synonym(ktw_b, typ_b).
synonym(ktw_a, typ_a).
synonym(rettungswagen_typ_c, rtw).

% Ausstattungskategorien
equipment_category(medical_equipment).
equipment_category(patient_transport).
equipment_category(technical_equipment).

equipment(oxygen_set, medical_equipment).
equipment(defibrillator, medical_equipment).
equipment(infusion_pump, medical_equipment).
equipment(stretcher, patient_transport).
equipment(wheelchair_ramp, patient_transport).
equipment(water_extinguisher, technical_equipment).
equipment(computer, technical_equipment).

equipment(immobilization_board, medical_equipment).
equipment(fire_blanket, technical_equipment).

equipment_profile(typ_a, [stretcher, oxygen_set, defibrillator]).
equipment_profile(typ_b, [stretcher, oxygen_set, defibrillator, infusion_pump]).
equipment_profile(typ_c, [stretcher, oxygen_set, defibrillator, infusion_pump, immobilization_board]).
equipment_profile(rettungswagen, [stretcher, oxygen_set, defibrillator, infusion_pump, immobilization_board, wheelchair_ramp]).

% Fahrzeuge und deren Ausstattungsdetails
has_equipment(ktw_a, stretcher).
has_equipment(ktw_a, oxygen_set).
has_equipment(ktw_a, defibrillator).

has_equipment(ktw_b, stretcher).
has_equipment(ktw_b, oxygen_set).
has_equipment(ktw_b, defibrillator).
has_equipment(ktw_b, infusion_pump).

has_equipment(ktw_c, stretcher).
has_equipment(ktw_c, oxygen_set).
has_equipment(ktw_c, defibrillator).
has_equipment(ktw_c, infusion_pump).
has_equipment(ktw_c, immobilization_board).

has_equipment(rtw, stretcher).
has_equipment(rtw, oxygen_set).
has_equipment(rtw, defibrillator).
has_equipment(rtw, infusion_pump).
has_equipment(rtw, immobilization_board).
has_equipment(rtw, wheelchair_ramp).

% Normbezogene Definitionen
defined_by(typ_a, din_en_1789).
defined_by(typ_b, din_en_1789).
defined_by(typ_c, din_en_1789).
defined_by(rettungswagen, din_en_1789_teil2).

% Regeln für KTW-Typen und Zuständigkeiten
supports_synonym(A, B) :- synonym(A, B).
supports_synonym(A, B) :- synonym(B, A).

% Ein Fahrzeug entspricht einem Typ, wenn es mindestens alle erforderlichen Ausrüstungsteile hat.
ktw_compliant(Vehicle, Type) :-
    ktw_type(Type),
    vehicle(Vehicle),
    equipment_profile(Type, RequiredEquipment),
    has_all_equipment(Vehicle, RequiredEquipment).

has_all_equipment(_, []).
has_all_equipment(Vehicle, [Item | Remaining]) :-
    has_equipment(Vehicle, Item),
    has_all_equipment(Vehicle, Remaining).

% Typ-Klassifikation nach Ausstattung und Norm
vehicle_type(Vehicle, typ_a) :-
    vehicle(Vehicle),
    has_all_equipment(Vehicle, [stretcher, oxygen_set, defibrillator]),
    defined_by(typ_a, din_en_1789).

vehicle_type(Vehicle, typ_b) :-
    vehicle(Vehicle),
    has_all_equipment(Vehicle, [stretcher, oxygen_set, defibrillator, infusion_pump]),
    defined_by(typ_b, din_en_1789).

vehicle_type(Vehicle, typ_c) :-
    vehicle(Vehicle),
    has_all_equipment(Vehicle, [stretcher, oxygen_set, defibrillator, infusion_pump, immobilization_board]),
    defined_by(typ_c, din_en_1789).

vehicle_type(Vehicle, rettungswagen) :-
    vehicle(Vehicle),
    has_all_equipment(Vehicle, [stretcher, oxygen_set, defibrillator, infusion_pump, immobilization_board, wheelchair_ramp]),
    defined_by(rettungswagen, din_en_1789_teil2).

% Zusatzregeln für Ausrüstung und Empfehlung
requires_equipment(typ_a, stretcher).
requires_equipment(typ_a, oxygen_set).
requires_equipment(typ_b, infusion_pump).
requires_equipment(typ_c, immobilization_board).
requires_equipment(rettungswagen, wheelchair_ramp).

recommended_for(medical_transport, typ_a).
recommended_for(high_risk_patient, typ_b).
recommended_for(critical_transport, typ_c).
recommended_for(emergency_service, rettungswagen).

equipped_for(Vehicle, Category) :-
    vehicle_type(Vehicle, Type),
    recommended_for(Category, Type).

% Beispielabfragen
% ?- ktw_compliant(ktw_c, typ_c).
% ?- vehicle_type(ktw_a, X).
% ?- equipped_for(rtw, emergency_service).
