interface ConfComponent {
  id: string;
  label: string;
}

interface Textbox extends ConfComponent {
  type: "textbox";
  text: string;
}

interface Checkbox extends ConfComponent {
  type: "checkbox";
  checked: boolean;
}

type Component = Checkbox | Textbox;

export interface ConfSection {
  id: string;
  title: string;
  children: Component[];
}

export interface Config {
  sections: ConfSection[];
}
