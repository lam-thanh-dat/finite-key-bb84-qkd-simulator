"""Small English-language desktop interface for the BB84 models."""

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import fields
from tkinter import messagebox, scrolledtext, ttk
from typing import Any

from .bb84_finite_key import FiniteKeyParameters, run_finite_key_trial
from .bb84_simulation import SimulationParameters, simulate_bb84


class ParameterForm(ttk.Frame):
    """Reusable parameter editor backed by a dataclass instance."""

    def __init__(
        self,
        master: tk.Misc,
        defaults: Any,
        labels: dict[str, str],
    ) -> None:
        super().__init__(master)
        self.defaults = defaults
        self.variables: dict[str, tk.StringVar] = {}

        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=12, pady=10)
        input_frame.columnconfigure(1, weight=1)

        for row, field in enumerate(fields(defaults)):
            value = getattr(defaults, field.name)
            label = labels.get(field.name, field.name.replace("_", " ").title())
            ttk.Label(input_frame, text=label).grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=(0, 10),
                pady=3,
            )
            variable = tk.StringVar(value=str(value))
            self.variables[field.name] = variable
            if field.name == "detection_model":
                widget = ttk.Combobox(
                    input_frame,
                    textvariable=variable,
                    values=("linear", "poisson"),
                    state="readonly",
                )
            else:
                widget = ttk.Entry(
                    input_frame,
                    textvariable=variable,
                )
            widget.grid(
                row=row,
                column=1,
                sticky=tk.EW,
                pady=3,
            )

        self.output = scrolledtext.ScrolledText(
            self,
            height=18,
            wrap=tk.WORD,
            font=("Consolas", 10),
        )
        self.output.pack(
            fill=tk.BOTH,
            expand=True,
            padx=12,
            pady=(0, 12),
        )

    def values(self) -> dict[str, Any]:
        converted: dict[str, Any] = {}
        for field in fields(self.defaults):
            text = self.variables[field.name].get().strip()
            default = getattr(self.defaults, field.name)
            if isinstance(default, bool):
                converted[field.name] = text.lower() in {
                    "1",
                    "true",
                    "yes",
                }
            elif isinstance(default, int):
                converted[field.name] = int(text)
            elif isinstance(default, float):
                converted[field.name] = float(text)
            else:
                converted[field.name] = text
        return converted

    def show_result(self, payload: dict[str, Any]) -> None:
        self.output.delete("1.0", tk.END)
        self.output.insert(
            tk.END,
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            ),
        )


class BB84Application(tk.Tk):
    """Top-level application with asymptotic and finite-size tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Finite-Key BB84 QKD Simulator")
        self.geometry("920x820")
        self.minsize(760, 680)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        common_labels = {
            "pulses": "Emitted signal slots",
            "mean_photon_number": "Mean photon number",
            "intrinsic_bit_fidelity": "Intrinsic bit fidelity",
            "receiver_efficiency": "Receiver efficiency",
            "intercept_resend_probability": ("Intercept-resend probability"),
            "leakage_fraction": "Heuristic leakage fraction",
            "error_correction_efficiency": ("Error-correction inefficiency"),
            "seed": "Random seed",
        }

        asymptotic_container = ttk.Frame(notebook)
        finite_container = ttk.Frame(notebook)
        notebook.add(
            asymptotic_container,
            text="Asymptotic Model",
        )
        notebook.add(
            finite_container,
            text="Finite-Size Model",
        )

        asymptotic_labels = {
            **common_labels,
            "parameter_estimation_bits": "Disclosed bits",
            "detection_model": "Detection model",
        }
        finite_labels = {
            **common_labels,
            "secrecy_epsilon": "Secrecy epsilon",
            "correctness_epsilon": "Correctness epsilon",
        }

        self.asymptotic_form = ParameterForm(
            asymptotic_container,
            SimulationParameters(),
            asymptotic_labels,
        )
        self.asymptotic_form.pack(fill=tk.BOTH, expand=True)
        ttk.Button(
            asymptotic_container,
            text="Run asymptotic simulation",
            command=self.run_asymptotic,
        ).pack(pady=(0, 10))

        self.finite_form = ParameterForm(
            finite_container,
            FiniteKeyParameters(),
            finite_labels,
        )
        self.finite_form.pack(fill=tk.BOTH, expand=True)
        ttk.Button(
            finite_container,
            text="Run finite-size simulation",
            command=self.run_finite,
        ).pack(pady=(0, 10))

        warning = (
            "Educational model only. The displayed key length is an "
            "information budget, not a cryptographic key."
        )
        ttk.Label(
            self,
            text=warning,
            anchor=tk.W,
        ).pack(fill=tk.X, padx=10, pady=5)

    def run_asymptotic(self) -> None:
        try:
            parameters = SimulationParameters(**self.asymptotic_form.values())
            result = simulate_bb84(parameters)
        except (TypeError, ValueError) as error:
            messagebox.showerror("Invalid parameters", str(error))
            return
        self.asymptotic_form.show_result(result.to_dict())

    def run_finite(self) -> None:
        try:
            parameters = FiniteKeyParameters(**self.finite_form.values())
            result = run_finite_key_trial(parameters)
        except (TypeError, ValueError) as error:
            messagebox.showerror("Invalid parameters", str(error))
            return
        self.finite_form.show_result(result.to_dict())


def main() -> None:
    app = BB84Application()
    app.mainloop()


if __name__ == "__main__":
    main()
