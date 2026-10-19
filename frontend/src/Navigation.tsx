import type { ReactElement } from "react";

export type Destination = "home" | "create" | "my" | "profile";

interface NavigationProps {
  active?: Destination;
  onSelect: (destination: Destination) => void;
}

function HomeIcon(): ReactElement {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V21h14V9.5" />
      <path d="M9 21v-6h6v6" />
    </svg>
  );
}

function ProfileIcon(): ReactElement {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5" />
    </svg>
  );
}

function CreateIcon(): ReactElement {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </svg>
  );
}

function MyConsultationsIcon(): ReactElement {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 8h8" />
      <path d="M8 12h8" />
      <path d="M8 16h5" />
    </svg>
  );
}

const DESTINATIONS: {
  key: Destination;
  label: string;
  icon: () => ReactElement;
}[] = [
  { key: "home", label: "Home", icon: HomeIcon },
  { key: "create", label: "Create", icon: CreateIcon },
  { key: "my", label: "My consultations", icon: MyConsultationsIcon },
  { key: "profile", label: "Profile", icon: ProfileIcon },
];

export function Navigation({ active, onSelect }: NavigationProps) {
  return (
    <nav className="navigation" aria-label="Primary">
      <ul className="navigation__list">
        {DESTINATIONS.map(({ key, label, icon: Icon }) => {
          const isActive = key === active;
          return (
            <li key={key} className="navigation__item">
              <button
                type="button"
                className="navigation__link"
                aria-current={isActive ? "page" : undefined}
                onClick={() => onSelect(key)}
              >
                <Icon />
                <span>{label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
