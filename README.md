# OpenSAFELY Reports

This is a Django app providing a location for viewing and exploring OpenSAFELY reports, both publicly available and content that limits access based on a user's NHS organisation membership.

Some content is publicly accessible; private content is accessed via authentication with NHS Identity via Open ID Connect. Authorisation is based on the NHS associated organisation information retrieved from NHS Identity.

For more information about internal user management policies, please see the team manual.


# For developers

Please see [the additional information](DEVELOPERS.md).


# About the OpenSAFELY framework

The OpenSAFELY framework is a Trusted Research Environment (TRE) for electronic
health records research in the NHS, with a focus on public accountability and
research quality.

Read more at [OpenSAFELY.org](https://opensafely.org).
