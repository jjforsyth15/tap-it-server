import vobject

from app.models.profile import Profile
from app.models.enums import ContactType
from app.services.files import sanitize_filename


# N is built from profile_name alone, never from profile.user -- a profile is
# free to use an alias/business name specifically to avoid publishing the
# account holder's real name, and the vCard must not leak it back out. Best
# effort split of "First Rest" into given/family since N has no single-field
# form; either way it stays within data the public profile already exposes.
def _name_from_profile(profile: Profile) -> vobject.vcard.Name:
    parts = profile.profile_name.split(maxsplit=1)
    given = parts[0] if parts else profile.profile_name
    family = parts[1] if len(parts) > 1 else ""
    return vobject.vcard.Name(family=family, given=given)


# vCard 3.0 for broad contact-app compatibility. FN is the display name
# (matches the public profile), N is the structured name most contact apps
# file the entry under. TYPE=PREF (a valid vCard 3.0 TYPE value, unlike v4's
# separate PREF parameter) marks whichever phone/email is_primary.
def build_vcard(profile: Profile) -> str:
    card = vobject.vCard()

    card.add("fn").value = profile.profile_name
    card.add("n").value = _name_from_profile(profile)

    if profile.subtitle:
        card.add("title").value = profile.subtitle

    if profile.organization:
        card.add("org").value = [profile.organization]

    if profile.profile_image_url:
        photo = card.add("photo")
        photo.value = profile.profile_image_url
        photo.value_param = "URI"

    for contact in profile.contact_info:
        if contact.contact_type == ContactType.phone:
            field = card.add("tel")
        elif contact.contact_type == ContactType.email:
            field = card.add("email")
        else:
            continue

        field.value = contact.value
        if contact.is_primary:
            field.type_param = ["PREF"]

    for link in profile.links:
        card.add("url").value = link.url

    return card.serialize()


def build_vcard_filename(profile: Profile) -> str:
    return f"{sanitize_filename(profile.profile_name, fallback='contact')}.vcf"
