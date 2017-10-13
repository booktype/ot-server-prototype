import json
import asyncio

from autobahn.asyncio.websocket import WebSocketServerProtocol

loop = asyncio.get_event_loop()


class WSServerProtocol(WebSocketServerProtocol):
    """
    Websocket server protocol.
    """
    CLIENTS = set()
    OT_STORAGE = {}

    def __init__(self):
        super(WSServerProtocol, self).__init__()
        self.user_id = None
        self.book_id = None
        self.document_id = None

    def _add_ot_change(self, ot):
        _ot = {
            'transformation': ot,
            'sent_to_client': [id(self)]
        }
        if self.document_id in self.OT_STORAGE:
            self.OT_STORAGE[self.document_id].append(_ot)
        else:
            self.OT_STORAGE[self.document_id] = [_ot]

        self._send_ot_change(self.document_id)

    def _sync_ot_changes(self, client):
        print('_sync_ot_changes self.OT_STORAGE', self.OT_STORAGE.keys())

        if self.document_id not in self.OT_STORAGE:
            return

        print('Im going to sync changes')

        changes = []
        limit = 20

        for ot in self.OT_STORAGE[client.document_id]:
            if limit:
                if id(client) not in ot['sent_to_client']:
                    changes.append(ot)
                    limit = - 1
            else:
                print('Sending sync package to document:', client.document_id, id(client))
                client.sendMessage(json.dumps({
                    'action': 'syncChanges',
                    'documentID': client.document_id,
                    'args': [change['transformation'] for change in changes]
                }).encode('utf8'), False)

                for ot in changes:
                    ot['sent_to_client'].append(id(client))

                limit = 20
                changes = []

        if changes:
            print('Sending sync package to document:', client.document_id, id(client))
            client.sendMessage(json.dumps({
                'action': 'syncChanges',
                'documentID': client.document_id,
                'args': [change['transformation'] for change in changes]
            }).encode('utf8'), False)

            for ot in changes:
                ot['sent_to_client'].append(id(client))

    def _send_ot_change(self, document_id):
        print('_send_ot_change self.OT_STORAGE', self.OT_STORAGE.keys())

        if document_id not in self.OT_STORAGE:
            return

        for ot in self.OT_STORAGE[document_id]:
            for client in self.CLIENTS:
                if client.document_id == document_id and id(client) not in ot['sent_to_client']:
                    print('Sending ot change to document:', client.document_id, id(client))
                    client.sendMessage(json.dumps({
                        'action': 'otChange',
                        'documentID': document_id,
                        'args': ot['transformation']
                    }).encode('utf8'), False)
                    ot['sent_to_client'].append(id(client))

    def onConnect(self, request):
        self.CLIENTS.add(self)

    def onMessage(self, payload, is_binary):
        payload_json = json.loads(payload)
        for client in self.CLIENTS:
            if client is self:

                if not payload_json['args'].get('documentID'):
                    break

                # INIT
                if payload_json['action'] == 'init':
                    print("INIT", id(client))
                    self.user_id = payload_json['args']['userID']
                    self.book_id = payload_json['args']['bookID']
                    self.document_id = payload_json['args']['documentID']
                # READY
                elif payload_json['action'] == 'ready':
                    self.document_id = payload_json['args']['documentID']
                    print("READY", id(client), self.document_id)
                    self._sync_ot_changes(client=self)

                break

        if payload_json['action'] == 'otChange':
            self._add_ot_change(payload_json['args'])

    def onClose(self, was_clean, code, reason):
        self.CLIENTS.remove(self)

    # comes from >>> class WebSocketAdapterProtocol(asyncio.Protocol):...
    def connection_made(self, transport):
        super(WSServerProtocol, self).connection_made(transport)

    def connection_lost(self, exc):
        super(WSServerProtocol, self).connection_lost(exc)
