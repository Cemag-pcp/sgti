from apps.accounts.models import RequesterProfile
from apps.assets.models import Asset

from .models import Ticket


def create_ticket_from_submission(form, *, created_by=None, requester_data=None):
    requester_data = requester_data or {}
    matricula = form.cleaned_data['matricula']
    full_name = form.cleaned_data['requester_name']

    requester, _ = RequesterProfile.objects.get_or_create(
        matricula=matricula,
        defaults={'full_name': full_name},
    )

    update_fields = []
    if requester.full_name != full_name:
        requester.full_name = full_name
        update_fields.append('full_name')

    requester_email = requester_data.get('email', '').strip()
    if requester_email and requester.email != requester_email:
        requester.email = requester_email
        update_fields.append('email')

    requester_phone = requester_data.get('phone', '').strip()
    if requester_phone and requester.phone != requester_phone:
        requester.phone = requester_phone
        update_fields.append('phone')

    requester_whatsapp_phone = requester_data.get('whatsapp_phone', '').strip()
    if requester_whatsapp_phone and requester.whatsapp_phone != requester_whatsapp_phone:
        requester.whatsapp_phone = requester_whatsapp_phone
        update_fields.append('whatsapp_phone')

    if update_fields:
        requester.save(update_fields=update_fields)

    ticket = form.save(commit=False)
    ticket.requester = requester
    if created_by is not None:
        ticket.created_by = created_by

    asset_tag = form.cleaned_data.get('asset_tag', '').strip()
    if asset_tag:
        try:
            ticket.asset = Asset.objects.get(asset_tag=asset_tag)
        except Asset.DoesNotExist:
            form.add_error('asset_tag', f'Tombamento "{asset_tag}" nÃ£o encontrado.')
            return None

    ticket.save()
    return ticket
