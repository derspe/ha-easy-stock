export interface Strings {
  editor: {
    title_label: string;
    display_currency: string;
    default_range: string;
    selected: string;
    drag_hint: string;
    add: string;
    no_sensors: string;
    setup_hint: string;
  };
  card: {
    not_found: string;
  };
}

const translations: Record<string, Strings> = {
  en: {
    editor: {
      title_label: "Title (optional)",
      display_currency: "Display currency",
      default_range: "Default time range",
      selected: "Selected",
      drag_hint: "drag to reorder",
      add: "Add",
      no_sensors: "No Easy Stock sensors found.",
      setup_hint: "Set up under Settings → Integrations → Easy Stock.",
    },
    card: { not_found: "Not found" },
  },
  de: {
    editor: {
      title_label: "Titel (optional)",
      display_currency: "Anzeigewährung",
      default_range: "Standard Zeitraum",
      selected: "Ausgewählt",
      drag_hint: "ziehen zum Sortieren",
      add: "Hinzufügen",
      no_sensors: "Keine Easy Stock Sensoren gefunden.",
      setup_hint: "Integration einrichten unter Einstellungen → Integrationen → Easy Stock.",
    },
    card: { not_found: "Nicht gefunden" },
  },
  fr: {
    editor: {
      title_label: "Titre (optionnel)",
      display_currency: "Devise d'affichage",
      default_range: "Période par défaut",
      selected: "Sélectionnés",
      drag_hint: "glisser pour réorganiser",
      add: "Ajouter",
      no_sensors: "Aucun capteur Easy Stock trouvé.",
      setup_hint: "Configurer sous Paramètres → Intégrations → Easy Stock.",
    },
    card: { not_found: "Introuvable" },
  },
  nl: {
    editor: {
      title_label: "Titel (optioneel)",
      display_currency: "Weergavevaluta",
      default_range: "Standaard tijdsbereik",
      selected: "Geselecteerd",
      drag_hint: "slepen om te sorteren",
      add: "Toevoegen",
      no_sensors: "Geen Easy Stock-sensoren gevonden.",
      setup_hint: "Instellen via Instellingen → Integraties → Easy Stock.",
    },
    card: { not_found: "Niet gevonden" },
  },
  es: {
    editor: {
      title_label: "Título (opcional)",
      display_currency: "Moneda de visualización",
      default_range: "Rango de tiempo predeterminado",
      selected: "Seleccionados",
      drag_hint: "arrastrar para ordenar",
      add: "Añadir",
      no_sensors: "No se encontraron sensores Easy Stock.",
      setup_hint: "Configurar en Ajustes → Integraciones → Easy Stock.",
    },
    card: { not_found: "No encontrado" },
  },
  it: {
    editor: {
      title_label: "Titolo (opzionale)",
      display_currency: "Valuta di visualizzazione",
      default_range: "Intervallo predefinito",
      selected: "Selezionati",
      drag_hint: "trascina per riordinare",
      add: "Aggiungi",
      no_sensors: "Nessun sensore Easy Stock trovato.",
      setup_hint: "Configurare in Impostazioni → Integrazioni → Easy Stock.",
    },
    card: { not_found: "Non trovato" },
  },
  pt: {
    editor: {
      title_label: "Título (opcional)",
      display_currency: "Moeda de exibição",
      default_range: "Intervalo padrão",
      selected: "Selecionados",
      drag_hint: "arrastar para reordenar",
      add: "Adicionar",
      no_sensors: "Nenhum sensor Easy Stock encontrado.",
      setup_hint: "Configurar em Definições → Integrações → Easy Stock.",
    },
    card: { not_found: "Não encontrado" },
  },
  pl: {
    editor: {
      title_label: "Tytuł (opcjonalny)",
      display_currency: "Waluta wyświetlania",
      default_range: "Domyślny zakres czasu",
      selected: "Wybrane",
      drag_hint: "przeciągnij, aby zmienić kolejność",
      add: "Dodaj",
      no_sensors: "Nie znaleziono czujników Easy Stock.",
      setup_hint: "Skonfiguruj w Ustawienia → Integracje → Easy Stock.",
    },
    card: { not_found: "Nie znaleziono" },
  },
  sv: {
    editor: {
      title_label: "Titel (valfritt)",
      display_currency: "Visningsvaluta",
      default_range: "Standardtidsintervall",
      selected: "Valda",
      drag_hint: "dra för att sortera",
      add: "Lägg till",
      no_sensors: "Inga Easy Stock-sensorer hittades.",
      setup_hint: "Konfigurera under Inställningar → Integrationer → Easy Stock.",
    },
    card: { not_found: "Hittades inte" },
  },
  da: {
    editor: {
      title_label: "Titel (valgfrit)",
      display_currency: "Visningsvaluta",
      default_range: "Standard tidsinterval",
      selected: "Valgte",
      drag_hint: "træk for at sortere",
      add: "Tilføj",
      no_sensors: "Ingen Easy Stock-sensorer fundet.",
      setup_hint: "Opsæt under Indstillinger → Integrationer → Easy Stock.",
    },
    card: { not_found: "Ikke fundet" },
  },
  nb: {
    editor: {
      title_label: "Tittel (valgfritt)",
      display_currency: "Visningsvaluta",
      default_range: "Standard tidsintervall",
      selected: "Valgte",
      drag_hint: "dra for å sortere",
      add: "Legg til",
      no_sensors: "Ingen Easy Stock-sensorer funnet.",
      setup_hint: "Konfigurer under Innstillinger → Integrasjoner → Easy Stock.",
    },
    card: { not_found: "Ikke funnet" },
  },
  fi: {
    editor: {
      title_label: "Otsikko (valinnainen)",
      display_currency: "Näyttövaluutta",
      default_range: "Oletusjaksovali",
      selected: "Valitut",
      drag_hint: "vedä järjestääksesi",
      add: "Lisää",
      no_sensors: "Easy Stock -antureita ei löydy.",
      setup_hint: "Määritä kohdassa Asetukset → Integraatiot → Easy Stock.",
    },
    card: { not_found: "Ei löydy" },
  },
  cs: {
    editor: {
      title_label: "Název (volitelný)",
      display_currency: "Zobrazovaná měna",
      default_range: "Výchozí časový rozsah",
      selected: "Vybrané",
      drag_hint: "přetáhněte pro seřazení",
      add: "Přidat",
      no_sensors: "Nebyly nalezeny žádné senzory Easy Stock.",
      setup_hint: "Nastavte v Nastavení → Integrace → Easy Stock.",
    },
    card: { not_found: "Nenalezeno" },
  },
  hu: {
    editor: {
      title_label: "Cím (opcionális)",
      display_currency: "Megjelenítési pénznem",
      default_range: "Alapértelmezett időtartomány",
      selected: "Kiválasztottak",
      drag_hint: "húzza a rendezéshez",
      add: "Hozzáadás",
      no_sensors: "Nem találhatók Easy Stock érzékelők.",
      setup_hint: "Állítsa be a Beállítások → Integrációk → Easy Stock menüpontban.",
    },
    card: { not_found: "Nem található" },
  },
  ru: {
    editor: {
      title_label: "Заголовок (необязательно)",
      display_currency: "Валюта отображения",
      default_range: "Временной диапазон по умолчанию",
      selected: "Выбранные",
      drag_hint: "перетащите для сортировки",
      add: "Добавить",
      no_sensors: "Датчики Easy Stock не найдены.",
      setup_hint: "Настройте в Настройки → Интеграции → Easy Stock.",
    },
    card: { not_found: "Не найдено" },
  },
  zh: {
    editor: {
      title_label: "标题（可选）",
      display_currency: "显示货币",
      default_range: "默认时间范围",
      selected: "已选择",
      drag_hint: "拖动以排序",
      add: "添加",
      no_sensors: "未找到 Easy Stock 传感器。",
      setup_hint: "在设置 → 集成 → Easy Stock 中进行配置。",
    },
    card: { not_found: "未找到" },
  },
  ja: {
    editor: {
      title_label: "タイトル（省略可）",
      display_currency: "表示通貨",
      default_range: "デフォルト期間",
      selected: "選択済み",
      drag_hint: "ドラッグして並び替え",
      add: "追加",
      no_sensors: "Easy Stock センサーが見つかりません。",
      setup_hint: "設定 → インテグレーション → Easy Stock で設定してください。",
    },
    card: { not_found: "見つかりません" },
  },
  ko: {
    editor: {
      title_label: "제목 (선택사항)",
      display_currency: "표시 통화",
      default_range: "기본 기간",
      selected: "선택됨",
      drag_hint: "드래그하여 정렬",
      add: "추가",
      no_sensors: "Easy Stock 센서를 찾을 수 없습니다.",
      setup_hint: "설정 → 통합 → Easy Stock에서 설정하세요.",
    },
    card: { not_found: "찾을 수 없음" },
  },
  tr: {
    editor: {
      title_label: "Başlık (isteğe bağlı)",
      display_currency: "Görüntüleme para birimi",
      default_range: "Varsayılan zaman aralığı",
      selected: "Seçilenler",
      drag_hint: "sıralamak için sürükle",
      add: "Ekle",
      no_sensors: "Easy Stock sensörü bulunamadı.",
      setup_hint: "Ayarlar → Entegrasyonlar → Easy Stock altında yapılandırın.",
    },
    card: { not_found: "Bulunamadı" },
  },
  ar: {
    editor: {
      title_label: "العنوان (اختياري)",
      display_currency: "عملة العرض",
      default_range: "النطاق الزمني الافتراضي",
      selected: "المحددة",
      drag_hint: "اسحب للترتيب",
      add: "إضافة",
      no_sensors: "لم يتم العثور على أجهزة استشعار Easy Stock.",
      setup_hint: "الإعداد في الإعدادات ← التكاملات ← Easy Stock.",
    },
    card: { not_found: "غير موجود" },
  },
};

export function t(lang: string): Strings {
  // Normalize: "zh-Hans" → "zh", "pt-BR" → "pt", "nb-NO" → "nb"
  const base = lang.split("-")[0].toLowerCase();
  return translations[base] ?? translations["en"];
}
