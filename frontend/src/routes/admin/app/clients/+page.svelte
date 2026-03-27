<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import { Input } from "$lib/components/ui/input";
    import * as Select from "$lib/components/ui/select";
    import * as Table from "$lib/components/ui/table";
    import * as Dialog from "$lib/components/ui/dialog";

    const { data, form } = $props();

    const clients = $derived(data.clients ?? []);
    const meta = $derived(
        data.meta ?? {
            search: "",
            sort_by: "name_client",
            sort_order: "asc",
            limit: 50,
            offset: 0,
            total: 0,
        },
    );

    const prevOffset = $derived(Math.max(0, Number(meta.offset) - Number(meta.limit)));
    const nextOffset = $derived(Number(meta.offset) + Number(meta.limit));
    const hasPrev = $derived(Number(meta.offset) > 0);
    const hasNext = $derived(nextOffset < Number(meta.total));

    let sortBy = $state("");
    let sortOrder = $state("");

    $effect(() => {
        if (!sortBy) sortBy = String(meta.sort_by ?? "name_client");
        if (!sortOrder) sortOrder = String(meta.sort_order ?? "asc");
    });
</script>

<section class="space-y-6 p-4 md:p-6">
    <header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
            <h1 class="text-2xl font-semibold">Clients</h1>
            <p class="text-muted-foreground text-sm">Manage master client records and their database connections.</p>
        </div>

        <Dialog.Root>
            <Dialog.Trigger>
                {#snippet child({ props })}
                    <Button {...props}>Create Client</Button>
                {/snippet}
            </Dialog.Trigger>
            <Dialog.Content>
                <Dialog.Header>
                    <Dialog.Title>Create Client</Dialog.Title>
                    <Dialog.Description>Add a new client record in master DB.</Dialog.Description>
                </Dialog.Header>

                <form method="POST" action="?/create" class="space-y-3">
                    <div class="space-y-1">
                        <label for="name_client" class="text-sm">Client Name</label>
                        <Input id="name_client" name="name_client" required />
                    </div>
                    <div class="space-y-1">
                        <label for="db_client" class="text-sm">DB URL</label>
                        <Input id="db_client" name="db_client" required />
                    </div>
                    <div class="space-y-1">
                        <label for="redis_client" class="text-sm">Redis URL</label>
                        <Input id="redis_client" name="redis_client" value="default" required />
                    </div>
                    <Dialog.Footer>
                        <Button type="submit">Save</Button>
                    </Dialog.Footer>
                </form>
            </Dialog.Content>
        </Dialog.Root>
    </header>

    <form method="GET" class="grid grid-cols-1 gap-2 rounded-lg border p-3 md:grid-cols-5">
        <Input name="search" placeholder="Search clients" value={meta.search} />
        <input type="hidden" name="sort_by" value={sortBy} />
        <Select.Root type="single" bind:value={sortBy}>
            <Select.Trigger class="w-full">
                {sortBy === "name_client"
                    ? "Name"
                    : sortBy === "db_client"
                        ? "DB URL"
                        : sortBy === "redis_client"
                            ? "Redis URL"
                            : "ID"}
            </Select.Trigger>
            <Select.Content>
                <Select.Item value="name_client" label="Name" />
                <Select.Item value="db_client" label="DB URL" />
                <Select.Item value="redis_client" label="Redis URL" />
                <Select.Item value="id" label="ID" />
            </Select.Content>
        </Select.Root>

        <input type="hidden" name="sort_order" value={sortOrder} />
        <Select.Root type="single" bind:value={sortOrder}>
            <Select.Trigger class="w-full">{sortOrder === "desc" ? "DESC" : "ASC"}</Select.Trigger>
            <Select.Content>
                <Select.Item value="asc" label="ASC" />
                <Select.Item value="desc" label="DESC" />
            </Select.Content>
        </Select.Root>
        <Input name="limit" type="number" min="1" max="200" value={String(meta.limit)} />
        <Button type="submit" variant="outline">Apply</Button>
    </form>

    {#if data.error}
        <p class="text-destructive text-sm">{data.error}</p>
    {/if}
    {#if form?.error}
        <p class="text-destructive text-sm">{form.message}</p>
    {/if}

    <Table.Root>
        <Table.Header>
            <Table.Row>
                <Table.Head>ID</Table.Head>
                <Table.Head>Client Name</Table.Head>
                <Table.Head>DB URL</Table.Head>
                <Table.Head>Redis URL</Table.Head>
                <Table.Head class="text-right">Actions</Table.Head>
            </Table.Row>
        </Table.Header>
        <Table.Body>
            {#if clients.length === 0}
                <Table.Row>
                    <Table.Cell colspan={5} class="text-muted-foreground text-center">No clients found.</Table.Cell>
                </Table.Row>
            {:else}
                {#each clients as client}
                    <Table.Row>
                        <Table.Cell>{client.id}</Table.Cell>
                        <Table.Cell>{client.name_client}</Table.Cell>
                        <Table.Cell class="max-w-[360px] truncate">{client.db_client}</Table.Cell>
                        <Table.Cell class="max-w-[260px] truncate">{client.redis_client}</Table.Cell>
                        <Table.Cell>
                            <div class="flex justify-end gap-2">
                                <Dialog.Root>
                                    <Dialog.Trigger>
                                        {#snippet child({ props })}
                                            <Button size="sm" variant="outline" {...props}>Edit</Button>
                                        {/snippet}
                                    </Dialog.Trigger>
                                    <Dialog.Content>
                                        <Dialog.Header>
                                            <Dialog.Title>Edit Client</Dialog.Title>
                                            <Dialog.Description>Update selected client data.</Dialog.Description>
                                        </Dialog.Header>
                                        <form method="POST" action="?/update" class="space-y-3">
                                            <input type="hidden" name="client_id" value={client.id} />
                                            <div class="space-y-1">
                                                <label class="text-sm" for={`name_client_${client.id}`}>Client Name</label>
                                                <Input id={`name_client_${client.id}`} name="name_client" value={client.name_client} />
                                            </div>
                                            <div class="space-y-1">
                                                <label class="text-sm" for={`db_client_${client.id}`}>DB URL</label>
                                                <Input id={`db_client_${client.id}`} name="db_client" value={client.db_client} />
                                            </div>
                                            <div class="space-y-1">
                                                <label class="text-sm" for={`redis_client_${client.id}`}>Redis URL</label>
                                                <Input id={`redis_client_${client.id}`} name="redis_client" value={client.redis_client} />
                                            </div>
                                            <Dialog.Footer>
                                                <Button type="submit">Update</Button>
                                            </Dialog.Footer>
                                        </form>
                                    </Dialog.Content>
                                </Dialog.Root>

                                <Dialog.Root>
                                    <Dialog.Trigger>
                                        {#snippet child({ props })}
                                            <Button size="sm" variant="destructive" {...props}>Delete</Button>
                                        {/snippet}
                                    </Dialog.Trigger>
                                    <Dialog.Content>
                                        <Dialog.Header>
                                            <Dialog.Title>Delete Client</Dialog.Title>
                                            <Dialog.Description>
                                                Are you sure you want to delete client {client.name_client}?
                                            </Dialog.Description>
                                        </Dialog.Header>
                                        <form method="POST" action="?/delete" class="space-y-3">
                                            <input type="hidden" name="client_id" value={client.id} />
                                            <Dialog.Footer>
                                                <Button type="submit" variant="destructive">Confirm Delete</Button>
                                            </Dialog.Footer>
                                        </form>
                                    </Dialog.Content>
                                </Dialog.Root>
                            </div>
                        </Table.Cell>
                    </Table.Row>
                {/each}
            {/if}
        </Table.Body>
    </Table.Root>

    <div class="flex items-center justify-between rounded-lg border p-3 text-sm">
        <p class="text-muted-foreground">
            Showing {clients.length} of {meta.total} clients
        </p>
        <div class="flex gap-2">
            <form method="GET">
                <input type="hidden" name="search" value={meta.search} />
                <input type="hidden" name="sort_by" value={meta.sort_by} />
                <input type="hidden" name="sort_order" value={meta.sort_order} />
                <input type="hidden" name="limit" value={meta.limit} />
                <input type="hidden" name="offset" value={prevOffset} />
                <Button type="submit" variant="outline" size="sm" disabled={!hasPrev}>Previous</Button>
            </form>
            <form method="GET">
                <input type="hidden" name="search" value={meta.search} />
                <input type="hidden" name="sort_by" value={meta.sort_by} />
                <input type="hidden" name="sort_order" value={meta.sort_order} />
                <input type="hidden" name="limit" value={meta.limit} />
                <input type="hidden" name="offset" value={nextOffset} />
                <Button type="submit" variant="outline" size="sm" disabled={!hasNext}>Next</Button>
            </form>
        </div>
    </div>
</section>
