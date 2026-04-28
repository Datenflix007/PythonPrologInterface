% Beispiel-Wissensbasis

person(alice).
person(bob).
person(charlie).

role(alice, developer).
role(bob, designer).
role(charlie, manager).

skill(alice, python).
skill(alice, prolog).
skill(bob, figma).
skill(charlie, planning).

project(alpha).
project(beta).

works_on(alice, alpha).
works_on(bob, alpha).
works_on(charlie, beta).

% Regel: Wer ist geeignet für ein Projekt?
suitable_for_project(Person, Project) :-
    person(Person),
    works_on(Person, Project).

% Regel: Wer kann eine Fähigkeit?
has_skill(Person, Skill) :-
    skill(Person, Skill).