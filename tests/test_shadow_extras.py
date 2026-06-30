"""Parked tests from test_coordinator.py in HA core. Add back in when adding additional features"""

# @pytest.mark.usefixtures("aioclient_mock_fixture")
# async def test_mqtt_shadow_merge_preserves_existing(
#     hass: HomeAssistant,
#     mock_config_entry: MockConfigEntry,
#     mock_provider: AsyncMock,
#     mock_get_iot_credentials: MagicMock,
#     mock_mqtt_client: MagicMock,
# ) -> None:
#     """Test that sparse shadow updates merge without losing existing state."""
#     await setup_integration(hass, mock_config_entry)

#     coordinator = mock_config_entry.runtime_data
#     assert coordinator.data["thing-001"].temperature_c == 22.5

#     # Send update with only alarm — temperature should be preserved
#     payload = json.dumps({"state": {"reported": {"coAlarmStatus": 4}}}).encode()
#     trigger_shadow_callback(
#         mock_mqtt_client,
#         "$aws/things/thing-001/shadow/update/accepted",
#         payload,
#     )
#     await hass.async_block_till_done()

#     assert coordinator.data["thing-001"].co_alarm_status is AlarmStatus.CRITICAL_ALARM
#     assert coordinator.data["thing-001"].temperature_c == 22.5


# @pytest.mark.usefixtures("aioclient_mock_fixture")
# async def test_mqtt_shadow_new_device(
#     hass: HomeAssistant,
#     mock_config_entry: MockConfigEntry,
#     mock_provider: AsyncMock,
#     mock_get_iot_credentials: MagicMock,
#     mock_mqtt_client: MagicMock,
# ) -> None:
#     """Test that a shadow message for an unknown device creates a new entry."""
#     await setup_integration(hass, mock_config_entry)

#     coordinator = mock_config_entry.runtime_data
#     assert "thing-999" not in coordinator.data

#     payload = json.dumps(
#         {"state": {"reported": {"coAlarmStatus": 1, "temperatureC": 18.0}}}
#     ).encode()
#     trigger_shadow_callback(
#         mock_mqtt_client,
#         "$aws/things/thing-999/shadow/get/accepted",
#         payload,
#     )
#     await hass.async_block_till_done()

#     assert "thing-999" in coordinator.data
#     assert coordinator.data["thing-999"].co_alarm_status is AlarmStatus.TEST
#     assert coordinator.data["thing-999"].temperature_c == 18.0


"""Parked tests from test_init.py in HA core. Add back in when adding additional features"""

# @pytest.mark.usefixtures("aioclient_mock_fixture")
# async def test_setup_seeds_shadow_from_discover(
# hass: HomeAssistant,
# mock_config_entry: MockConfigEntry,
# mock_provider: AsyncMock,
# mock_get_iot_credentials: MagicMock,
# mock_mqtt_client: MagicMock,
# ) -> None:
# """Test that initial shadow state is seeded from device discovery."""
# await setup_integration(hass, mock_config_entry)
#
# coordinator = mock_config_entry.runtime_data
# assert "thing-001" in coordinator.data
# shadow = coordinator.data["thing-001"]
# assert shadow.co_alarm_status.value == 0
# assert shadow.heat_alarm_status.value == 0
# assert shadow.smoke_alarm_status.value == 0
# assert shadow.temperature_c == 22.5
# assert shadow.humidity == 45
