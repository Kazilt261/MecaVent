<script lang="ts">
    import {
        Sidebar,
        SidebarContent,
        SidebarFooter,
        SidebarGroup,
        SidebarGroupContent,
        SidebarGroupLabel,
        SidebarHeader,
        SidebarMenu,
        SidebarMenuButton,
        SidebarMenuItem,
        SidebarProvider,
    } from "$lib/components/ui/sidebar";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";

    import { Button } from "$lib/components/ui/button";
    import { toggleMode } from "mode-watcher";

    interface ItemMenu {
        label: string;
        path: string;
        icon: string;
    }

    const menuItems: ItemMenu[] = [];

    const { data } = $props();
    const user = $derived(data.user);
</script>

<SidebarProvider>
    <Sidebar>
        <SidebarHeader>
            <div class="px-4 py-2">
                <h1 class="text-xl font-bold">Admin Panel</h1>
            </div>
        </SidebarHeader>

        <SidebarContent>
            <SidebarGroup>
                <SidebarGroupLabel>Menu</SidebarGroupLabel>
                <SidebarGroupContent>
                    <SidebarMenu>
                        {#each menuItems as item}
                            <SidebarMenuItem>
                                <SidebarMenuButton class="space-x-2">
                                    {#snippet child({ props })}
                                        <a href={item.path} class="w-full block px-2 py-1" {...props}>
                                            <span>{item.icon}</span>
                                            <span>{item.label}</span>
                                        </a>
                                    {/snippet}
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        {/each}
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
            <SidebarMenu>
                <SidebarMenuItem>
                    <DropdownMenu.Root>
                        <DropdownMenu.Trigger>
                            {#snippet child({ props })}
                                <Button variant="ghost" class="w-full justify-start" {...props}>
                                    {user.username}
                                </Button>
                            {/snippet}
                        </DropdownMenu.Trigger>
                        <DropdownMenu.Content>
                            <DropdownMenu.Item>
                                {#snippet child({ props })}
                                    <a href="/admin/profile" class="w-full block px-2 py-1" {...props}> Profile </a>
                                {/snippet}
                            </DropdownMenu.Item>
                            <DropdownMenu.Item onclick={toggleMode}>Toggle theme</DropdownMenu.Item>
                            <DropdownMenu.Item>
                                {#snippet child({ props })}
                                    <a href="/logout" class="w-full block px-2 py-1" {...props}> Logout </a>
                                {/snippet}
                            </DropdownMenu.Item>
                        </DropdownMenu.Content>
                    </DropdownMenu.Root>
                </SidebarMenuItem>
            </SidebarMenu>
        </SidebarFooter>
    </Sidebar>
</SidebarProvider>
