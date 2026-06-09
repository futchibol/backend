"""
FIFA World Cup 2026 seed data
48 teams, 12 groups (A–L), 72 group-stage matches + knockout placeholders
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Team, Match, MatchStage


TEAMS = [
    # Group A
    {"name": "Estados Unidos", "code": "USA", "flag": "🇺🇸", "group": "A", "confederation": "CONCACAF"},
    {"name": "Panamá",         "code": "PAN", "flag": "🇵🇦", "group": "A", "confederation": "CONCACAF"},
    {"name": "Camerún",        "code": "CMR", "flag": "🇨🇲", "group": "A", "confederation": "CAF"},
    {"name": "Corea del Sur",  "code": "KOR", "flag": "🇰🇷", "group": "A", "confederation": "AFC"},
    # Group B
    {"name": "México",         "code": "MEX", "flag": "🇲🇽", "group": "B", "confederation": "CONCACAF"},
    {"name": "Honduras",       "code": "HON", "flag": "🇭🇳", "group": "B", "confederation": "CONCACAF"},
    {"name": "Uruguay",        "code": "URU", "flag": "🇺🇾", "group": "B", "confederation": "CONMEBOL"},
    {"name": "Argelia",        "code": "ALG", "flag": "🇩🇿", "group": "B", "confederation": "CAF"},
    # Group C
    {"name": "Canadá",         "code": "CAN", "flag": "🇨🇦", "group": "C", "confederation": "CONCACAF"},
    {"name": "Costa Rica",     "code": "CRC", "flag": "🇨🇷", "group": "C", "confederation": "CONCACAF"},
    {"name": "Japón",          "code": "JPN", "flag": "🇯🇵", "group": "C", "confederation": "AFC"},
    {"name": "Marruecos",      "code": "MAR", "flag": "🇲🇦", "group": "C", "confederation": "CAF"},
    # Group D
    {"name": "Argentina",      "code": "ARG", "flag": "🇦🇷", "group": "D", "confederation": "CONMEBOL"},
    {"name": "Polonia",        "code": "POL", "flag": "🇵🇱", "group": "D", "confederation": "UEFA"},
    {"name": "Nigeria",        "code": "NGA", "flag": "🇳🇬", "group": "D", "confederation": "CAF"},
    {"name": "Indonesia",      "code": "IDN", "flag": "🇮🇩", "group": "D", "confederation": "AFC"},
    # Group E
    {"name": "Brasil",         "code": "BRA", "flag": "🇧🇷", "group": "E", "confederation": "CONMEBOL"},
    {"name": "Chile",          "code": "CHI", "flag": "🇨🇱", "group": "E", "confederation": "CONMEBOL"},
    {"name": "Serbia",         "code": "SRB", "flag": "🇷🇸", "group": "E", "confederation": "UEFA"},
    {"name": "Irán",           "code": "IRN", "flag": "🇮🇷", "group": "E", "confederation": "AFC"},
    # Group F
    {"name": "Francia",        "code": "FRA", "flag": "🇫🇷", "group": "F", "confederation": "UEFA"},
    {"name": "Ecuador",        "code": "ECU", "flag": "🇪🇨", "group": "F", "confederation": "CONMEBOL"},
    {"name": "Costa de Marfil","code": "CIV", "flag": "🇨🇮", "group": "F", "confederation": "CAF"},
    {"name": "Australia",      "code": "AUS", "flag": "🇦🇺", "group": "F", "confederation": "AFC"},
    # Group G
    {"name": "España",         "code": "ESP", "flag": "🇪🇸", "group": "G", "confederation": "UEFA"},
    {"name": "Colombia",       "code": "COL", "flag": "🇨🇴", "group": "G", "confederation": "CONMEBOL"},
    {"name": "Egipto",         "code": "EGY", "flag": "🇪🇬", "group": "G", "confederation": "CAF"},
    {"name": "Dinamarca",      "code": "DEN", "flag": "🇩🇰", "group": "G", "confederation": "UEFA"},
    # Group H
    {"name": "Inglaterra",     "code": "ENG", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "group": "H", "confederation": "UEFA"},
    {"name": "Jamaica",        "code": "JAM", "flag": "🇯🇲", "group": "H", "confederation": "CONCACAF"},
    {"name": "Senegal",        "code": "SEN", "flag": "🇸🇳", "group": "H", "confederation": "CAF"},
    {"name": "Austria",        "code": "AUT", "flag": "🇦🇹", "group": "H", "confederation": "UEFA"},
    # Group I
    {"name": "Alemania",       "code": "GER", "flag": "🇩🇪", "group": "I", "confederation": "UEFA"},
    {"name": "Venezuela",      "code": "VEN", "flag": "🇻🇪", "group": "I", "confederation": "CONMEBOL"},
    {"name": "Sudáfrica",      "code": "RSA", "flag": "🇿🇦", "group": "I", "confederation": "CAF"},
    {"name": "Jordania",       "code": "JOR", "flag": "🇯🇴", "group": "I", "confederation": "AFC"},
    # Group J
    {"name": "Países Bajos",   "code": "NED", "flag": "🇳🇱", "group": "J", "confederation": "UEFA"},
    {"name": "Croacia",        "code": "CRO", "flag": "🇭🇷", "group": "J", "confederation": "UEFA"},
    {"name": "Ghana",          "code": "GHA", "flag": "🇬🇭", "group": "J", "confederation": "CAF"},
    {"name": "Iraq",           "code": "IRQ", "flag": "🇮🇶", "group": "J", "confederation": "AFC"},
    # Group K
    {"name": "Portugal",       "code": "POR", "flag": "🇵🇹", "group": "K", "confederation": "UEFA"},
    {"name": "Ucrania",        "code": "UKR", "flag": "🇺🇦", "group": "K", "confederation": "UEFA"},
    {"name": "Arabia Saudita", "code": "KSA", "flag": "🇸🇦", "group": "K", "confederation": "AFC"},
    {"name": "Rep. Checa",     "code": "CZE", "flag": "🇨🇿", "group": "K", "confederation": "UEFA"},
    # Group L
    {"name": "Italia",         "code": "ITA", "flag": "🇮🇹", "group": "L", "confederation": "UEFA"},
    {"name": "Bélgica",        "code": "BEL", "flag": "🇧🇪", "group": "L", "confederation": "UEFA"},
    {"name": "Suiza",          "code": "SUI", "flag": "🇨🇭", "group": "L", "confederation": "UEFA"},
    {"name": "Nueva Zelanda",  "code": "NZL", "flag": "🇳🇿", "group": "L", "confederation": "OFC"},
]

# Venues for World Cup 2026 (USA/Mexico/Canada)
VENUES = {
    "A": ("SoFi Stadium", "Los Ángeles"),
    "B": ("Estadio Azteca", "Ciudad de México"),
    "C": ("BMO Field", "Toronto"),
    "D": ("MetLife Stadium", "Nueva York"),
    "E": ("AT&T Stadium", "Dallas"),
    "F": ("Stade Olympique", "Montreal"),
    "G": ("Rose Bowl", "Los Ángeles"),
    "H": ("Arrowhead Stadium", "Kansas City"),
    "I": ("NRG Stadium", "Houston"),
    "J": ("Levi's Stadium", "San Francisco"),
    "K": ("Estadio BBVA", "Monterrey"),
    "L": ("Lincoln Financial Field", "Filadelfia"),
}

# Group stage schedule: MD = match day
# Format: (group_letter, team1_idx_in_group, team2_idx_in_group, days_offset)
# teams in group are indexed 0-3
GROUP_MATCHES = [
    # MD1
    ("A", 0, 1, 0),   # USA vs Panama        Jun 11
    ("A", 2, 3, 0),   # Cameroon vs South Korea
    ("B", 0, 1, 1),   # Mexico vs Honduras   Jun 12
    ("B", 2, 3, 1),   # Uruguay vs Algeria
    ("C", 0, 1, 2),   # Canada vs Costa Rica Jun 13
    ("C", 2, 3, 2),   # Japan vs Morocco
    ("D", 0, 1, 3),   # Argentina vs Poland  Jun 14
    ("D", 2, 3, 3),   # Nigeria vs Indonesia
    ("E", 0, 1, 4),   # Brazil vs Chile      Jun 15
    ("E", 2, 3, 4),   # Serbia vs Iran
    ("F", 0, 1, 5),   # France vs Ecuador    Jun 16
    ("F", 2, 3, 5),   # Ivory Coast vs Australia
    ("G", 0, 1, 6),   # Spain vs Colombia    Jun 17
    ("G", 2, 3, 6),   # Egypt vs Denmark
    ("H", 0, 1, 7),   # England vs Jamaica   Jun 18
    ("H", 2, 3, 7),   # Senegal vs Austria
    ("I", 0, 1, 8),   # Germany vs Venezuela Jun 19
    ("I", 2, 3, 8),   # South Africa vs Jordan
    ("J", 0, 1, 9),   # Netherlands vs Croatia Jun 20
    ("J", 2, 3, 9),   # Ghana vs Iraq
    ("K", 0, 1, 10),  # Portugal vs Ukraine  Jun 21
    ("K", 2, 3, 10),  # Saudi Arabia vs Czech Republic
    ("L", 0, 1, 11),  # Italy vs Belgium     Jun 22
    ("L", 2, 3, 11),  # Switzerland vs New Zealand
    # MD2
    ("A", 0, 2, 12),  # USA vs Cameroon      Jun 23
    ("A", 1, 3, 12),  # Panama vs South Korea
    ("B", 0, 2, 13),  # Mexico vs Uruguay    Jun 24
    ("B", 1, 3, 13),  # Honduras vs Algeria
    ("C", 0, 2, 14),  # Canada vs Japan      Jun 25
    ("C", 1, 3, 14),  # Costa Rica vs Morocco
    ("D", 0, 2, 15),  # Argentina vs Nigeria Jun 26
    ("D", 1, 3, 15),  # Poland vs Indonesia
    ("E", 0, 2, 16),  # Brazil vs Serbia     Jun 27
    ("E", 1, 3, 16),  # Chile vs Iran
    ("F", 0, 2, 17),  # France vs Ivory Coast Jun 28
    ("F", 1, 3, 17),  # Ecuador vs Australia
    ("G", 0, 2, 18),  # Spain vs Egypt       Jun 29
    ("G", 1, 3, 18),  # Colombia vs Denmark
    ("H", 0, 2, 19),  # England vs Senegal   Jun 30
    ("H", 1, 3, 19),  # Jamaica vs Austria
    ("I", 0, 2, 20),  # Germany vs South Africa Jul 1
    ("I", 1, 3, 20),  # Venezuela vs Jordan
    ("J", 0, 2, 21),  # Netherlands vs Ghana Jul 2
    ("J", 1, 3, 21),  # Croatia vs Iraq
    ("K", 0, 2, 22),  # Portugal vs Saudi Arabia Jul 3
    ("K", 1, 3, 22),  # Ukraine vs Czech Republic
    ("L", 0, 2, 23),  # Italy vs Switzerland Jul 4
    ("L", 1, 3, 23),  # Belgium vs New Zealand
    # MD3 (simultaneous within group)
    ("A", 0, 3, 24),  # USA vs South Korea   Jul 5
    ("A", 1, 2, 24),  # Panama vs Cameroon
    ("B", 0, 3, 25),  # Mexico vs Algeria    Jul 6
    ("B", 1, 2, 25),  # Honduras vs Uruguay
    ("C", 0, 3, 26),  # Canada vs Morocco    Jul 7
    ("C", 1, 2, 26),  # Costa Rica vs Japan
    ("D", 0, 3, 27),  # Argentina vs Indonesia Jul 8
    ("D", 1, 2, 27),  # Poland vs Nigeria
    ("E", 0, 3, 28),  # Brazil vs Iran       Jul 9
    ("E", 1, 2, 28),  # Chile vs Serbia
    ("F", 0, 3, 29),  # France vs Australia  Jul 10
    ("F", 1, 2, 29),  # Ecuador vs Ivory Coast
    ("G", 0, 3, 30),  # Spain vs Denmark     Jul 11
    ("G", 1, 2, 30),  # Colombia vs Egypt
    ("H", 0, 3, 31),  # England vs Austria   Jul 12
    ("H", 1, 2, 31),  # Jamaica vs Senegal
    ("I", 0, 3, 32),  # Germany vs Jordan    Jul 13
    ("I", 1, 2, 32),  # Venezuela vs South Africa
    ("J", 0, 3, 33),  # Netherlands vs Iraq  Jul 14
    ("J", 1, 2, 33),  # Croatia vs Ghana
    ("K", 0, 3, 34),  # Portugal vs Czech Republic Jul 15
    ("K", 1, 2, 34),  # Ukraine vs Saudi Arabia
    ("L", 0, 3, 35),  # Italy vs New Zealand Jul 16
    ("L", 1, 2, 35),  # Belgium vs Switzerland
]

# Knockout round placeholder matches (teams TBD)
KNOCKOUT_MATCHES = [
    # Round of 32 (16 matches) - July 29 - Aug 1
    (MatchStage.R32, "1A vs 2C",   "2B vs 1D",  39, "MetLife Stadium",    "Nueva York"),
    (MatchStage.R32, "1B vs 2D",   "2A vs 1C",  39, "AT&T Stadium",       "Dallas"),
    (MatchStage.R32, "1E vs 2G",   "2F vs 1H",  40, "Rose Bowl",          "Los Ángeles"),
    (MatchStage.R32, "1F vs 2H",   "2E vs 1G",  40, "SoFi Stadium",       "Los Ángeles"),
    (MatchStage.R32, "1I vs 2K",   "2J vs 1L",  41, "NRG Stadium",        "Houston"),
    (MatchStage.R32, "1J vs 2L",   "2I vs 1K",  41, "Levi's Stadium",     "San Francisco"),
    (MatchStage.R32, "3A/B/C/D",   "3E/F/G/H",  42, "Estadio Azteca",     "Ciudad de México"),
    (MatchStage.R32, "3I/J/K/L",   "Mejor 3°",  42, "BMO Field",          "Toronto"),
    # Round of 16 (8 matches) - Aug 4-7
    (MatchStage.R16, "G R32-1",    "G R32-2",   54, "MetLife Stadium",    "Nueva York"),
    (MatchStage.R16, "G R32-3",    "G R32-4",   55, "Rose Bowl",          "Los Ángeles"),
    (MatchStage.R16, "G R32-5",    "G R32-6",   56, "AT&T Stadium",       "Dallas"),
    (MatchStage.R16, "G R32-7",    "G R32-8",   57, "Estadio Azteca",     "Ciudad de México"),
    (MatchStage.R16, "G R32-9",    "G R32-10",  54, "SoFi Stadium",       "Los Ángeles"),
    (MatchStage.R16, "G R32-11",   "G R32-12",  55, "NRG Stadium",        "Houston"),
    (MatchStage.R16, "G R32-13",   "G R32-14",  56, "BMO Field",          "Toronto"),
    (MatchStage.R16, "G R32-15",   "G R32-16",  57, "Levi's Stadium",     "San Francisco"),
    # Quarterfinals (4 matches) - Aug 10-12
    (MatchStage.QF, "G R16-1",    "G R16-2",    61, "MetLife Stadium",    "Nueva York"),
    (MatchStage.QF, "G R16-3",    "G R16-4",    62, "Rose Bowl",          "Los Ángeles"),
    (MatchStage.QF, "G R16-5",    "G R16-6",    63, "AT&T Stadium",       "Dallas"),
    (MatchStage.QF, "G R16-7",    "G R16-8",    64, "Estadio Azteca",     "Ciudad de México"),
    # Semifinals (2 matches) - Aug 16-17
    (MatchStage.SF, "G QF-1",     "G QF-2",     68, "MetLife Stadium",    "Nueva York"),
    (MatchStage.SF, "G QF-3",     "G QF-4",     69, "Rose Bowl",          "Los Ángeles"),
    # Third place - Aug 20
    (MatchStage.THIRD, "Perdedor SF-1", "Perdedor SF-2", 72, "AT&T Stadium", "Dallas"),
    # Final - Aug 21
    (MatchStage.FINAL, "Ganador SF-1",  "Ganador SF-2",  73, "MetLife Stadium", "Nueva York"),
]


def seed_wc2026(db: Session):
    if db.query(Team).count() > 0:
        return  # Already seeded

    start_date = datetime(2026, 6, 11, 18, 0, 0)  # June 11, 2026

    # Insert teams
    team_map: dict[str, dict[str, int]] = {}  # group_letter -> {idx -> team_id}
    for t in TEAMS:
        team = Team(
            name=t["name"],
            code=t["code"],
            flag_emoji=t["flag"],
            group_letter=t["group"],
            confederation=t["confederation"],
        )
        db.add(team)
        db.flush()
        if t["group"] not in team_map:
            team_map[t["group"]] = {}
        count = len(team_map[t["group"]])
        team_map[t["group"]][count] = team.id

    match_number = 1

    # Group stage matches
    for (grp, t1_idx, t2_idx, days_offset) in GROUP_MATCHES:
        venue, city = VENUES.get(grp, ("TBD", "TBD"))
        scheduled = start_date + timedelta(days=days_offset)
        match = Match(
            match_number=match_number,
            stage=MatchStage.GROUP,
            group_letter=grp,
            team1_id=team_map[grp][t1_idx],
            team2_id=team_map[grp][t2_idx],
            scheduled_at=scheduled,
            venue=venue,
            city=city,
        )
        db.add(match)
        match_number += 1

    # Knockout matches
    for (stage, ph1, ph2, days_offset, venue, city) in KNOCKOUT_MATCHES:
        scheduled = start_date + timedelta(days=days_offset)
        match = Match(
            match_number=match_number,
            stage=stage,
            team1_placeholder=ph1,
            team2_placeholder=ph2,
            scheduled_at=scheduled,
            venue=venue,
            city=city,
        )
        db.add(match)
        match_number += 1

    db.commit()
    print(f"✅ Seeded {match_number - 1} matches and {len(TEAMS)} teams for WC 2026")
