from collections.abc import Callable

from tmis.platform_sdk.sdk.ports import PluginPort

PluginFactory = Callable[[], PluginPort]
"""A zero-argument constructor for a plugin instance — registered at
process startup (an ordinary Python import, see
`tmis.platform_sdk.examples`), never resolved from a string or
executed from uploaded source. TMIS deliberately does not support
dynamically importing or `eval`/`exec`-ing untrusted plugin code in
process: real third-party code isolation belongs at the deployment
layer (a container/VM per plugin, see `tmis.platform.deployment`,
Sprint 10), not inside the Python interpreter that also runs the rest
of TMIS. See docs/65-architecture-platform-sdk.md — "Ce que ce sprint
ne fait pas"."""
