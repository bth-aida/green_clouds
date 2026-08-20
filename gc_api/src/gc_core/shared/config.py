"""Config parameters for models"""

### external imports
from enum import Enum
import logging
from pydantic import BaseModel, Field
from typing import Annotated, Any, Literal, Sequence, Union

### internal imports
from gc_core.shared.model_definitions import get_model_names

### config logger
lg = logging.getLogger("app_logger")


# config keys
class NumConfig(str, Enum):
    # MinBufferSize = "Minimum buffer size"
    # MaxBufferSize = "Maximum buffer size"
    BufferSize = "Buffer size"
    UpdateInterval = "Update interval"


# options keys
class Option(str, Enum):
    Stream = "Stream model"


# default values
num_config_default: dict[str, int] = {
    # NumConfig.MinBufferSize: 2000,
    # NumConfig.MaxBufferSize: 3000,
    NumConfig.BufferSize: 3000,
    NumConfig.UpdateInterval: 200,
}


### config components
class ConfigComponent(BaseModel):
    """Abstract class representing a frontend component"""

    id: str
    label: str


class Numbox(ConfigComponent):
    """A textbox for integer input"""

    type: Literal["textbox"] = "textbox"
    text: str


class Checkbox(ConfigComponent):
    """One checkbox that can be toggled"""

    type: Literal["checkbox"] = "checkbox"
    checked: bool = True


### component
Component = Annotated[Union[Checkbox, Numbox], Field(discriminator="type")]


class ConfigSection(BaseModel):
    """Config sections can contain multiple components"""

    id: str
    title: str
    children: Sequence[Component]


class FormConfig(BaseModel):
    """A defined config, that can contain multiple config sections"""

    sections: list[ConfigSection]


### get config
def get_frontend_config(config_values: dict[str, int | str | bool]) -> FormConfig:
    """Returns a ConfigSection that can be viewed in the frontend.
    The structure of the frontend should be defined here.
    """

    # a group of checkboxes, one for each model
    model_group: list[Checkbox] = []
    models = get_model_names()
    for model in models:
        model_checked = config_values.get(model, True)
        if not isinstance(model_checked, bool):
            model_checked = False
        model_group.append(Checkbox(id=model, label=model, checked=model_checked))

    model_selection = ConfigSection(
        id="model_selection", title="Model Selection", children=model_group
    )

    # parse config
    num_config = parse_config(config_values)

    # a group of numboxes
    stream_parameters = ConfigSection(
        id="stream_parameters",
        title="Stream Parameters",
        children=[
            Numbox(id=key, label=key, text=str(value))
            for key, value in num_config.items()
        ],
    )

    # a group of checkboxes for options

    stream_checked = config_values.get(Option.Stream, True)
    if not isinstance(stream_checked, bool):
        stream_checked = False

    option_group = ConfigSection(
        id="options",
        title="Options",
        children=[
            Checkbox(
                id=Option.Stream,
                label=Option.Stream,
                checked=stream_checked,
            )
        ],
    )

    return FormConfig(sections=[model_selection, stream_parameters, option_group])


def get_config_defaults() -> dict[str, Any]:
    """Return a key-value dict with the config defaults variables"""
    config = get_frontend_config({})
    config_values: dict[str, Any] = {}
    for section in config.sections:
        for child in section.children:
            if isinstance(child, Checkbox):
                config_values[child.id] = child.checked
            else:
                config_values[child.id] = child.text

    return config_values


def parse_config(config: dict[str, Any]) -> dict[str, int]:
    """Parse config received from webapp, return corrected version"""
    config_nums: dict[str, int] = {}
    for key in num_config_default.keys():
        try:
            config_value = config.get(key)
            config_nums[key] = int(config_value)  # type: ignore
        except Exception:
            config_nums[key] = num_config_default[key]

    return config_nums
