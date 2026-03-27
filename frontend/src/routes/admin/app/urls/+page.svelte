<script lang="ts">
	import { Button } from "$lib/components/ui/button";
	import { Input } from "$lib/components/ui/input";
	import * as Select from "$lib/components/ui/select";
	import * as Table from "$lib/components/ui/table";
	import * as Dialog from "$lib/components/ui/dialog";

	const { data, form } = $props();

	const clients = $derived(data.clients ?? []);
	const urls = $derived(data.urls ?? []);
	const selectedClientId = $derived(data.selectedClientId);

	const clientsMeta = $derived(
		data.clientsMeta ?? {
			search: "",
			sort_by: "name_client",
			sort_order: "asc",
			limit: 50,
			offset: 0,
			total: 0,
		}
	);

	const urlsMeta = $derived(
		data.urlsMeta ?? {
			search: "",
			sort_by: "id",
			sort_order: "asc",
			limit: 50,
			offset: 0,
			total: 0,
		}
	);

	const selectedClient = $derived(clients.find((item) => item.id === selectedClientId) ?? null);

	const prevUrlsOffset = $derived(Math.max(0, Number(urlsMeta.offset) - Number(urlsMeta.limit)));
	const nextUrlsOffset = $derived(Number(urlsMeta.offset) + Number(urlsMeta.limit));
	const hasPrevUrls = $derived(Number(urlsMeta.offset) > 0);
	const hasNextUrls = $derived(nextUrlsOffset < Number(urlsMeta.total));

	let filterClientId = $state("");
	let urlsSortBy = $state("");
	let urlsSortOrder = $state("");
	let createClientId = $state("");

	const createClient = $derived(clients.find((item) => String(item.id) === createClientId) ?? null);

	$effect(() => {
		if (!filterClientId) filterClientId = String(selectedClientId ? selectedClientId : "");
		if (!urlsSortBy) urlsSortBy = String(urlsMeta.sort_by ?? "id");
		if (!urlsSortOrder) urlsSortOrder = String(urlsMeta.sort_order ?? "asc");
	});
</script>

<section class="space-y-6 p-4 md:p-6">
	<header class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
		<div>
			<h1 class="text-2xl font-semibold">Client URLs</h1>
			<p class="text-muted-foreground text-sm">Manage URLs per client from the master registry.</p>
		</div>

		<Dialog.Root>
			<Dialog.Trigger>
				{#snippet child({ props })}
					<Button {...props} disabled={clients.length === 0}>Create URL</Button>
				{/snippet}
			</Dialog.Trigger>
			<Dialog.Content>
				<Dialog.Header>
					<Dialog.Title>Create URL</Dialog.Title>
					<Dialog.Description>
						Select a client and add a URL associated with it.
					</Dialog.Description>
				</Dialog.Header>

				<form method="POST" action="?/create" class="space-y-3">
					<input type="hidden" name="client_id" value={createClientId} />
					<div class="space-y-1">
						<p class="text-sm">Client</p>
						<Select.Root type="single" bind:value={createClientId}>
							<Select.Trigger class="w-full">
								{createClient ? createClient.name_client : "Select client"}
							</Select.Trigger>
							<Select.Content>
								{#each clients as client}
									<Select.Item value={String(client.id)} label={client.name_client} />
								{/each}
							</Select.Content>
						</Select.Root>
					</div>
					<div class="space-y-1">
						<label for="urls" class="text-sm">URL</label>
						<Input id="urls" name="urls" placeholder="https://client.example.com" required />
					</div>
					<Dialog.Footer>
						<Button type="submit" disabled={!createClientId}>Save</Button>
					</Dialog.Footer>
				</form>
			</Dialog.Content>
		</Dialog.Root>
	</header>

	<form method="GET" class="grid grid-cols-1 gap-2 rounded-lg border p-3 md:grid-cols-6">
		<input type="hidden" name="client_id" value={filterClientId} />
		<Select.Root type="single" bind:value={filterClientId}>
			<Select.Trigger class="w-full">
				{selectedClient ? selectedClient.name_client : "Select client"}
			</Select.Trigger>
			<Select.Content>
				{#each clients as client}
					<Select.Item value={String(client.id)} label={client.name_client} />
				{/each}
			</Select.Content>
		</Select.Root>

		<Input name="urls_search" placeholder="Search URLs" value={urlsMeta.search} />

		<input type="hidden" name="urls_sort_by" value={urlsSortBy} />
		<Select.Root type="single" bind:value={urlsSortBy}>
			<Select.Trigger class="w-full">{urlsSortBy === "urls" ? "URL" : "ID"}</Select.Trigger>
			<Select.Content>
				<Select.Item value="id" label="ID" />
				<Select.Item value="urls" label="URL" />
			</Select.Content>
		</Select.Root>

		<input type="hidden" name="urls_sort_order" value={urlsSortOrder} />
		<Select.Root type="single" bind:value={urlsSortOrder}>
			<Select.Trigger class="w-full">{urlsSortOrder === "desc" ? "DESC" : "ASC"}</Select.Trigger>
			<Select.Content>
				<Select.Item value="asc" label="ASC" />
				<Select.Item value="desc" label="DESC" />
			</Select.Content>
		</Select.Root>

		<Input name="urls_limit" type="number" min="1" max="200" value={String(urlsMeta.limit)} />

		<Button type="submit" variant="outline">Apply</Button>

		<input type="hidden" name="clients_search" value={clientsMeta.search} />
		<input type="hidden" name="clients_sort_by" value={clientsMeta.sort_by} />
		<input type="hidden" name="clients_sort_order" value={clientsMeta.sort_order} />
		<input type="hidden" name="clients_limit" value={clientsMeta.limit} />
		<input type="hidden" name="clients_offset" value={clientsMeta.offset} />
		<input type="hidden" name="urls_offset" value={0} />
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
				<Table.Head>Client ID</Table.Head>
				<Table.Head>URL</Table.Head>
				<Table.Head class="text-right">Actions</Table.Head>
			</Table.Row>
		</Table.Header>
		<Table.Body>
			{#if urls.length === 0}
				<Table.Row>
					<Table.Cell colspan={4} class="text-muted-foreground text-center">No URLs found for this client.</Table.Cell>
				</Table.Row>
			{:else}
				{#each urls as item}
					<Table.Row>
						<Table.Cell>{item.id}</Table.Cell>
						<Table.Cell>{item.id_app}</Table.Cell>
						<Table.Cell class="max-w-[520px] truncate">{item.urls}</Table.Cell>
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
											<Dialog.Title>Edit URL</Dialog.Title>
											<Dialog.Description>Update URL for selected client.</Dialog.Description>
										</Dialog.Header>
										<form method="POST" action="?/update" class="space-y-3">
											<input type="hidden" name="client_id" value={selectedClientId ?? ""} />
											<input type="hidden" name="url_id" value={item.id} />
											<div class="space-y-1">
												<label class="text-sm" for={`url_${item.id}`}>URL</label>
												<Input id={`url_${item.id}`} name="urls" value={item.urls} required />
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
											<Dialog.Title>Delete URL</Dialog.Title>
											<Dialog.Description>Confirm URL deletion.</Dialog.Description>
										</Dialog.Header>
										<form method="POST" action="?/delete" class="space-y-3">
											<input type="hidden" name="client_id" value={selectedClientId ?? ""} />
											<input type="hidden" name="url_id" value={item.id} />
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
			Showing {urls.length} of {urlsMeta.total} URLs
		</p>
		<div class="flex gap-2">
			<form method="GET">
				<input type="hidden" name="client_id" value={selectedClientId ?? ""} />
				<input type="hidden" name="urls_search" value={urlsMeta.search} />
				<input type="hidden" name="urls_sort_by" value={urlsMeta.sort_by} />
				<input type="hidden" name="urls_sort_order" value={urlsMeta.sort_order} />
				<input type="hidden" name="urls_limit" value={urlsMeta.limit} />
				<input type="hidden" name="urls_offset" value={prevUrlsOffset} />

				<input type="hidden" name="clients_search" value={clientsMeta.search} />
				<input type="hidden" name="clients_sort_by" value={clientsMeta.sort_by} />
				<input type="hidden" name="clients_sort_order" value={clientsMeta.sort_order} />
				<input type="hidden" name="clients_limit" value={clientsMeta.limit} />
				<input type="hidden" name="clients_offset" value={clientsMeta.offset} />

				<Button type="submit" variant="outline" size="sm" disabled={!hasPrevUrls}>Previous</Button>
			</form>
			<form method="GET">
				<input type="hidden" name="client_id" value={selectedClientId ?? ""} />
				<input type="hidden" name="urls_search" value={urlsMeta.search} />
				<input type="hidden" name="urls_sort_by" value={urlsMeta.sort_by} />
				<input type="hidden" name="urls_sort_order" value={urlsMeta.sort_order} />
				<input type="hidden" name="urls_limit" value={urlsMeta.limit} />
				<input type="hidden" name="urls_offset" value={nextUrlsOffset} />

				<input type="hidden" name="clients_search" value={clientsMeta.search} />
				<input type="hidden" name="clients_sort_by" value={clientsMeta.sort_by} />
				<input type="hidden" name="clients_sort_order" value={clientsMeta.sort_order} />
				<input type="hidden" name="clients_limit" value={clientsMeta.limit} />
				<input type="hidden" name="clients_offset" value={clientsMeta.offset} />

				<Button type="submit" variant="outline" size="sm" disabled={!hasNextUrls}>Next</Button>
			</form>
		</div>
	</div>
</section>
