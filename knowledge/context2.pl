% context2_smart.pl
% Überarbeitete DIN / KTW Wissensbasis
% Ziele:
% - alte Fakten und zentrale Prädikate bleiben kompatibel
% - Eingaben funktionieren als Atom oder Liste
% - Synonyme werden automatisch normalisiert
% - gerichtete und ungerichtete Beziehungen können abgefragt werden
% - Klassifikation liefert den spezifischsten passenden Fahrzeugtyp

% ------------------------------------------------------------
% Basisfakten
% ------------------------------------------------------------

% Allgemeine Fahrzeugdaten
vehicle(ktw_a).          % Krankentransportwagen Typ A
vehicle(ktw_b).          % Krankentransportwagen Typ B
vehicle(ktw_c).          % Krankentransportwagen Typ C
vehicle(rtw).            % Rettungswagen
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
synonym(notfall_ktw, typ_b).

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

% Ausstattungsprofile je Typ
equipment_profile(typ_a, [stretcher, oxygen_set, defibrillator]).
equipment_profile(typ_b, [stretcher, oxygen_set, defibrillator, infusion_pump]).
equipment_profile(typ_c, [stretcher, oxygen_set, defibrillator, infusion_pump, immobilization_board]).
equipment_profile(rettungswagen, [stretcher, oxygen_set, defibrillator, infusion_pump, immobilization_board, wheelchair_ramp]).

% Fahrzeuge und Ausstattung
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

has_equipment(notfall_ktw, stretcher).
has_equipment(notfall_ktw, oxygen_set).
has_equipment(notfall_ktw, defibrillator).
has_equipment(notfall_ktw, infusion_pump).

% Normbezogene Definitionen
defined_by(typ_a, din_en_1789).
defined_by(typ_b, din_en_1789).
defined_by(typ_c, din_en_1789).
defined_by(rettungswagen, din_en_1789_teil2).

% Zusatzregeln für Empfehlung und Rückgriff
requires_equipment(typ_a, stretcher).
requires_equipment(typ_a, oxygen_set).
requires_equipment(typ_a, defibrillator).
requires_equipment(typ_b, infusion_pump).
requires_equipment(typ_c, immobilization_board).
requires_equipment(rettungswagen, wheelchair_ramp).

recommended_for(medical_transport, typ_a).
recommended_for(high_risk_patient, typ_b).
recommended_for(critical_transport, typ_c).
recommended_for(emergency_service, rettungswagen).

% ------------------------------------------------------------
% Hilfsprädikate: Listen, Normalisierung, Synonyme
% ------------------------------------------------------------

% Eigener member, damit keine Abhängigkeit von Bibliotheken entsteht.
my_member(X, [X | _]).
my_member(X, [_ | Tail]) :-
    my_member(X, Tail).

is_list([]).
is_list([_ | _]).

% supports_synonym/2 bleibt kompatibel zur alten Variante.
supports_synonym(A, B) :- synonym(A, B).
supports_synonym(A, B) :- synonym(B, A).

% normalize_entity(+Input, -Canonical)
% Akzeptiert bekannte Synonyme, Typen, Fahrzeuge, Normen, Ausstattung und Kategorien.
normalize_entity(Input, Canonical) :-
    nonvar(Input),
    synonym(Input, Next),
    !,
    normalize_entity(Next, Canonical).
normalize_entity(Input, Canonical) :-
    nonvar(Input),
    synonym(Previous, Input),
    ktw_type(Input),
    !,
    Canonical = Input,
    Previous \= Input.
normalize_entity(Input, Input) :-
    nonvar(Input),
    ( vehicle(Input)
    ; ktw_type(Input)
    ; norm(Input)
    ; equipment(Input, _)
    ; equipment_category(Input)
    ; recommended_for(Input, _)
    ),
    !.
normalize_entity(Input, Input).

normalize_list([], []).
normalize_list([X | Xs], [Y | Ys]) :-
    normalize_entity(X, Y),
    normalize_list(Xs, Ys).

% map_result(+PredicateName, +Inputs, -Outputs)
% Für einfache zweistellige Prädikate, die auch Listen akzeptieren sollen.
map_result(_, [], []).
map_result(Pred, [X | Xs], [Y | Ys]) :-
    Goal =.. [Pred, X, Y],
    call(Goal),
    map_result(Pred, Xs, Ys).

% ------------------------------------------------------------
% Normabfragen: Atom und Liste
% ------------------------------------------------------------

% Alte Abfrage bleibt gültig:
% ?- ktw_norm(typ_a, Norm).
% Neue Abfrage:
% ?- ktw_norm([ktw_a, ktw_b, ktw_c], Norms).
ktw_norm(Input, Norms) :-
    is_list(Input),
    !,
    map_result(ktw_norm, Input, Norms).
ktw_norm(Input, Norm) :-
    normalize_entity(Input, Type),
    my_member(Type, [typ_a, typ_b, typ_c]),
    defined_by(Type, Norm).

% Auch bewusst explizit als Listenprädikat nutzbar.
ktw_norm_list(Inputs, Norms) :-
    ktw_norm(Inputs, Norms).

% ------------------------------------------------------------
% Ausstattung und Compliance: Atom und Liste
% ------------------------------------------------------------

has_all_equipment(_, []).
has_all_equipment(VehicleInput, [ItemInput | Remaining]) :-
    normalize_entity(VehicleInput, Vehicle),
    normalize_entity(ItemInput, Item),
    has_equipment(Vehicle, Item),
    has_all_equipment(Vehicle, Remaining).

missing_equipment(VehicleInput, TypeInput, Missing) :-
    normalize_entity(VehicleInput, Vehicle),
    normalize_entity(TypeInput, Type),
    equipment_profile(Type, Required),
    missing_from_vehicle(Vehicle, Required, Missing).

missing_from_vehicle(_, [], []).
missing_from_vehicle(Vehicle, [Item | Rest], Missing) :-
    has_equipment(Vehicle, Item),
    !,
    missing_from_vehicle(Vehicle, Rest, Missing).
missing_from_vehicle(Vehicle, [Item | Rest], [Item | MissingRest]) :-
    missing_from_vehicle(Vehicle, Rest, MissingRest).

ktw_compliant(VehicleInputs, Types) :-
    is_list(VehicleInputs),
    !,
    map_result(ktw_compliant, VehicleInputs, Types).
ktw_compliant(VehicleInput, Type) :-
    normalize_entity(VehicleInput, Vehicle),
    ktw_type(Type),
    vehicle(Vehicle),
    equipment_profile(Type, RequiredEquipment),
    has_all_equipment(Vehicle, RequiredEquipment).

compatible_vehicle_type(VehicleInput, Type) :-
    ktw_compliant(VehicleInput, Type).

% ------------------------------------------------------------
% Spezifische Klassifikation
% ------------------------------------------------------------

% Rangfolge: je höher, desto spezifischer.
type_rank(typ_a, 1).
type_rank(typ_b, 2).
type_rank(typ_c, 3).
type_rank(rettungswagen, 4).

more_specific(Type, OtherType) :-
    type_rank(Type, Rank),
    type_rank(OtherType, OtherRank),
    Rank > OtherRank.

most_specific_type(VehicleInput, Type) :-
    ktw_compliant(VehicleInput, Type),
    \+ (ktw_compliant(VehicleInput, OtherType), more_specific(OtherType, Type)).

% vehicle_type/2 bleibt als zentrale alte Abfrage erhalten, liefert aber jetzt den besten Typ.
vehicle_type(VehicleInputs, Types) :-
    is_list(VehicleInputs),
    !,
    map_result(vehicle_type, VehicleInputs, Types).
vehicle_type(VehicleInput, Type) :-
    most_specific_type(VehicleInput, Type).

classify_vehicle(VehicleInputs, Types) :-
    is_list(VehicleInputs),
    !,
    map_result(classify_vehicle, VehicleInputs, Types).
classify_vehicle(VehicleInput, Type) :-
    normalize_entity(VehicleInput, Vehicle),
    vehicle(Vehicle),
    vehicle_type(Vehicle, Type),
    !.
classify_vehicle(VehicleInput, unknown) :-
    normalize_entity(VehicleInput, Vehicle),
    vehicle(Vehicle).

% ------------------------------------------------------------
% Empfehlungen
% ------------------------------------------------------------

equipped_for(VehicleInputs, Categories) :-
    is_list(VehicleInputs),
    !,
    map_result(equipped_for, VehicleInputs, Categories).
equipped_for(VehicleInput, Category) :-
    classify_vehicle(VehicleInput, Type),
    recommended_for(Category, Type).

recommend_vehicle_for(CategoryInput, Type) :-
    normalize_entity(CategoryInput, Category),
    recommended_for(Category, Type).

recommend_vehicle_for_list([], []).
recommend_vehicle_for_list([Category | Rest], [Type | Types]) :-
    recommend_vehicle_for(Category, Type),
    recommend_vehicle_for_list(Rest, Types).

% ------------------------------------------------------------
% Gerichtete und ungerichtete Beziehungen
% ------------------------------------------------------------

% directed_relation(Source, Relation, Target)
% Semantik: Source --Relation--> Target
directed_relation(typ_a, defined_by, din_en_1789).
directed_relation(typ_b, defined_by, din_en_1789).
directed_relation(typ_c, defined_by, din_en_1789).
directed_relation(rettungswagen, defined_by, din_en_1789_teil2).

directed_relation(typ_a, requires, stretcher).
directed_relation(typ_a, requires, oxygen_set).
directed_relation(typ_a, requires, defibrillator).
directed_relation(typ_b, requires, infusion_pump).
directed_relation(typ_c, requires, immobilization_board).
directed_relation(rettungswagen, requires, wheelchair_ramp).

directed_relation(medical_transport, recommended_type, typ_a).
directed_relation(high_risk_patient, recommended_type, typ_b).
directed_relation(critical_transport, recommended_type, typ_c).
directed_relation(emergency_service, recommended_type, rettungswagen).

directed_relation(ktw_a, classified_as, typ_a).
directed_relation(ktw_b, classified_as, typ_b).
directed_relation(ktw_c, classified_as, typ_c).
directed_relation(rtw, classified_as, rettungswagen).
directed_relation(notfall_ktw, classified_as, typ_b).

% undirected_relation(A, Relation, B)
% Semantik: Richtung egal, z.B. Synonyme oder Kategoriezuordnung.
undirected_relation(rtw, synonym_of, rettungswagen).
undirected_relation(ktw_c, synonym_of, typ_c).
undirected_relation(ktw_b, synonym_of, typ_b).
undirected_relation(ktw_a, synonym_of, typ_a).
undirected_relation(rettungswagen_typ_c, synonym_of, rtw).
undirected_relation(notfall_ktw, synonym_of, typ_b).

undirected_relation(oxygen_set, belongs_to_category, medical_equipment).
undirected_relation(defibrillator, belongs_to_category, medical_equipment).
undirected_relation(infusion_pump, belongs_to_category, medical_equipment).
undirected_relation(immobilization_board, belongs_to_category, medical_equipment).
undirected_relation(stretcher, belongs_to_category, patient_transport).
undirected_relation(wheelchair_ramp, belongs_to_category, patient_transport).
undirected_relation(water_extinguisher, belongs_to_category, technical_equipment).
undirected_relation(computer, belongs_to_category, technical_equipment).
undirected_relation(fire_blanket, belongs_to_category, technical_equipment).

% relation/3 fragt Beziehungen richtungsrobust ab:
% - gerichtete Relationen bleiben gerichtet
% - ungerichtete Relationen funktionieren in beiden Richtungen
relation(AInput, Relation, BInput) :-
    normalize_entity(AInput, A),
    normalize_entity(BInput, B),
    directed_relation(A, Relation, B).
relation(AInput, Relation, BInput) :-
    normalize_entity(AInput, A),
    normalize_entity(BInput, B),
    undirected_relation(A, Relation, B).
relation(AInput, Relation, BInput) :-
    normalize_entity(AInput, A),
    normalize_entity(BInput, B),
    undirected_relation(B, Relation, A).

% relation/4 macht die Direktionalität explizit.
% Direction = directed | undirected | reverse_undirected
relation(AInput, Relation, BInput, directed) :-
    normalize_entity(AInput, A),
    normalize_entity(BInput, B),
    directed_relation(A, Relation, B).
relation(AInput, Relation, BInput, undirected) :-
    normalize_entity(AInput, A),
    normalize_entity(BInput, B),
    undirected_relation(A, Relation, B).
relation(AInput, Relation, BInput, reverse_undirected) :-
    normalize_entity(AInput, A),
    normalize_entity(BInput, B),
    undirected_relation(B, Relation, A).

% Eingabe als Liste von Paaren: relations([(ktw_a, typ_a), ...], synonym_of, Directions).
relations([], _, []).
relations([(A, B) | Rest], Relation, [Direction | Directions]) :-
    relation(A, Relation, B, Direction),
    relations(Rest, Relation, Directions).

% ------------------------------------------------------------
% Generische Wissensabfragen
% ------------------------------------------------------------

% fact/1: prüft, ob eine Entität bekannt ist.
fact(EntityInput) :-
    normalize_entity(EntityInput, Entity),
    ( vehicle(Entity)
    ; ktw_type(Entity)
    ; norm(Entity)
    ; equipment(Entity, _)
    ; equipment_category(Entity)
    ).

% facts/1: alle Listenelemente müssen bekannt sein.
facts([]).
facts([X | Xs]) :-
    fact(X),
    facts(Xs).

% know/3: generischer Einstiegspunkt für viele Fragen.
know(Entity, norm, Norm) :- ktw_norm(Entity, Norm).
know(Entity, type, Type) :- classify_vehicle(Entity, Type).
know(Entity, compatible_type, Type) :- compatible_vehicle_type(Entity, Type).
know(Entity, equipment, Equipment) :-
    normalize_entity(Entity, Vehicle),
    has_equipment(Vehicle, Equipment).
know(Entity, equipment_profile, EquipmentList) :-
    normalize_entity(Entity, Type),
    equipment_profile(Type, EquipmentList).
know(Entity, missing_for_type(Type), Missing) :-
    missing_equipment(Entity, Type, Missing).
know(Entity, recommended_for, Category) :- equipped_for(Entity, Category).
know(Entity, relation(Relation), Target) :- relation(Entity, Relation, Target).

% know_list(+Inputs, +Question, -Answers)
know_list([], _, []).
know_list([Input | Inputs], Question, [Answer | Answers]) :-
    know(Input, Question, Answer),
    know_list(Inputs, Question, Answers).

% ------------------------------------------------------------
% Beispielabfragen
% ------------------------------------------------------------

% Alte Abfragen:
% ?- classify_vehicle(ktw_c, Type).
% ?- vehicle_type(ktw_c, Type).
% ?- equipped_for(ktw_c, Category).
% ?- ktw_norm(typ_a, Norm).
%
% Neue Abfragen:
% ?- ktw_norm([ktw_a, ktw_b, ktw_c], Norms).
% ?- classify_vehicle([ktw_a, ktw_b, ktw_c, rtw], Types).
% ?- vehicle_type([ktw_a, ktw_b, ktw_c, rtw], Types).
% ?- relation(ktw_a, synonym_of, typ_a, Direction).
% ?- relation(typ_a, defined_by, din_en_1789, Direction).
% ?- relations([(ktw_a, typ_a), (typ_b, ktw_b)], synonym_of, Directions).
% ?- know(ktw_c, norm, Norm).
% ?- know(ktw_c, type, Type).
% ?- know(ktw_c, missing_for_type(rettungswagen), Missing).
% ?- know_list([ktw_a, ktw_b, ktw_c], norm, Norms).
