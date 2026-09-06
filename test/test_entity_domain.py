"""Tests for Home Assistant entity ID domains."""

from types import SimpleNamespace
from unittest.mock import Mock

from custom_components.xiaomi_home.miot.miot_device import (
    MIoTActionEntity,
    MIoTEntityData,
    MIoTEventEntity,
    MIoTPropertyEntity,
    MIoTServiceEntity,
)
from custom_components.xiaomi_home.miot.miot_spec import (
    MIoTSpecAction,
    MIoTSpecEvent,
    MIoTSpecProperty,
    MIoTSpecService,
)


def fake_device() -> SimpleNamespace:
    """Create a device with entity ID generators that record their domain."""
    return SimpleNamespace(
        online=True,
        name="Test device",
        miot_client=SimpleNamespace(main_loop=None),
        gen_service_entity_id=Mock(return_value="switch.test"),
        gen_prop_entity_id=Mock(return_value="select.test"),
        gen_event_entity_id=Mock(return_value="event.test"),
        gen_action_entity_id=Mock(return_value="button.test"),
    )


def fake_service() -> MIoTSpecService:
    """Create a minimal MIoT service for entity construction."""
    service = object.__new__(MIoTSpecService)
    service.iid = 2
    service.name = "test_service"
    service.description = "test_service"
    service.description_trans = "Test service"
    service.proprietary = False
    service.entity_category = None
    return service


def test_service_entity_uses_platform_domain() -> None:
    """A service entity uses its platform instead of the integration domain."""
    device = fake_device()
    service = fake_service()

    MIoTServiceEntity(device, MIoTEntityData("switch", service))

    device.gen_service_entity_id.assert_called_once_with(
        "switch", siid=2, description="test_service"
    )


def test_property_entity_uses_platform_domain() -> None:
    """A property entity uses its platform instead of the integration domain."""
    device = fake_device()
    prop = object.__new__(MIoTSpecProperty)
    prop.service = fake_service()
    prop.iid = 3
    prop.name = "test_property"
    prop.description_trans = "Test property"
    prop.proprietary = False
    prop.platform = "select"
    prop.device_class = None
    prop.value_range = None
    prop.value_list = None

    MIoTPropertyEntity(device, prop)

    device.gen_prop_entity_id.assert_called_once_with(
        ha_domain="select", spec_name="test_property", siid=2, piid=3
    )


def test_event_entity_uses_platform_domain() -> None:
    """An event entity uses its platform instead of the integration domain."""
    class TestEventEntity(MIoTEventEntity):
        """Concrete MIoT event entity for testing."""

        def on_event_occurred(self, name: str, arguments: dict | None = None) -> None:
            pass

    device = fake_device()
    event = object.__new__(MIoTSpecEvent)
    event.service = fake_service()
    event.iid = 4
    event.name = "test_event"
    event.description_trans = "Test event"
    event.proprietary = False
    event.platform = "event"
    event.device_class = None
    event.argument = []

    TestEventEntity(device, event)

    device.gen_event_entity_id.assert_called_once_with(
        ha_domain="event", spec_name="test_event", siid=2, eiid=4
    )


def test_action_entity_uses_platform_domain() -> None:
    """An action entity uses its platform instead of the integration domain."""
    device = fake_device()
    action = object.__new__(MIoTSpecAction)
    action.service = fake_service()
    action.iid = 5
    action.name = "test_action"
    action.description_trans = "Test action"
    action.proprietary = False
    action.platform = "button"
    action.device_class = None

    MIoTActionEntity(device, action)

    device.gen_action_entity_id.assert_called_once_with(
        ha_domain="button", spec_name="test_action", siid=2, aiid=5
    )
