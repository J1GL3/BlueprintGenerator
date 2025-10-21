def on_generate(self):
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    self.update_selected_count()
    if not assets:
        unreal.log_warning("⚠️ No assets selected.")
        return

    unreal.log(f"🛠 Generating blueprints for {len(assets)} assets...")
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    for asset in assets:
        try:
            bp_name = f"{asset.get_name()}_BP"
            unique_name = tools.create_unique_asset_name(f"{DESTINATION_FOLDER}/{bp_name}", "")
            bp_name = unique_name[1] if isinstance(unique_name, (list, tuple)) else unique_name

            factory = unreal.BlueprintFactory()
            factory.set_editor_property("ParentClass", unreal.Actor)
            bp = tools.create_asset(bp_name, DESTINATION_FOLDER, unreal.Blueprint, factory)
            if not bp:
                unreal.log_warning(f"❌ Failed to create blueprint for {asset.get_name()}")
                continue

            # ---------- create node + template ----------
            scs = bp.simple_construction_script
            node = None
            component_template = None

            if isinstance(asset, unreal.StaticMesh):
                node = scs.add_node(unreal.StaticMeshComponent)
                component_template = node.get_editor_property("component_template")

                # assign mesh and force the template to register the change
                component_template.set_editor_property("static_mesh", asset)
                try:
                    component_template.post_edit_change()
                except Exception:
                    # some builds may not expose post_edit_change(); safe to ignore
                    pass

                unreal.log(f"📦 set static mesh on template: {asset.get_name()}")

            elif isinstance(asset, unreal.SkeletalMesh):
                node = scs.add_node(unreal.SkeletalMeshComponent)
                component_template = node.get_editor_property("component_template")
                component_template.set_editor_property("skeletal_mesh", asset)
                try:
                    component_template.post_edit_change()
                except Exception:
                    pass
                unreal.log(f"🦴 set skeletal mesh on template: {asset.get_name()}")

            else:
                node = scs.add_node(unreal.SceneComponent)
                component_template = node.get_editor_property("component_template")
                unreal.log(f"🧩 added SceneComponent for {asset.get_name()}")

            # ---------- set node as root ----------
            if node:
                scs.set_root_node(node)
                # attempt to set CDO root (helps some versions)
                try:
                    generated = getattr(bp, "generated_class", None) or getattr(bp, "GeneratedClass", None)
                    if generated:
                        cdo = generated.get_default_object()
                        # Only set if empty
                        current_root = None
                        try:
                            current_root = cdo.get_editor_property("root_component")
                        except Exception:
                            pass
                        if not current_root:
                            cdo.set_editor_property("root_component", component_template)
                except Exception as e:
                    unreal.log_warning(f"Could not set CDO root: {e}")

            # ---------- apply UI-driven properties ----------
            if component_template:
                if hasattr(component_template, "enable_gravity"):
                    component_template.set_editor_property("enable_gravity", self.gravity_cb.isChecked())
                if hasattr(component_template, "generate_overlap_events"):
                    component_template.set_editor_property("generate_overlap_events", self.gen_overlap_cb.isChecked())
                if hasattr(component_template, "use_continuous_collision_detection"):
                    component_template.set_editor_property("use_continuous_collision_detection", self.ccd_cb.isChecked())
                if hasattr(component_template, "collision_complexity"):
                    if self.simple_collision_cb.isChecked():
                        component_template.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                    else:
                        component_template.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
                preset = self.collision_combo.currentText()
                if hasattr(component_template, "collision_profile_name"):
                    component_template.set_editor_property("collision_profile_name", unreal.Name(preset))

            # ---------- Compile / refresh / force CDO rebuild ----------
            try:
                # compile the blueprint
                # KismetEditorUtilities.compile_blueprint is generally reliable for editor scripts
                unreal.KismetEditorUtilities.compile_blueprint(bp)
            except Exception:
                try:
                    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
                except Exception:
                    unreal.log_warning("Could not call compile_blueprint via KismetEditorUtilities or BlueprintEditorLibrary.")

            # refresh nodes
            try:
                unreal.BlueprintEditorLibrary.refresh_all_nodes(bp)
            except Exception:
                pass

            # rerun construction on the CDO so editor shows the template
            try:
                generated = getattr(bp, "generated_class", None) or getattr(bp, "GeneratedClass", None)
                if generated:
                    cdo = generated.get_default_object()
                    try:
                        cdo.rerun_construction_scripts()
                    except Exception:
                        # fallback: call a method that should exist on UE objects
                        pass
            except Exception:
                pass

            # ---------- Save and open for inspection ----------
            bp.mark_package_dirty()
            unreal.EditorAssetLibrary.save_loaded_asset(bp)

            # Debug: print SCS nodes and template mesh name (if any)
            try:
                nodes = scs.get_all_nodes()
                unreal.log(f"DEBUG: SCS nodes count for {bp.get_name()}: {len(nodes)}")
                for n in nodes:
                    tmpl = n.get_editor_property("component_template")
                    name_prop = None
                    try:
                        # attempt to read static_mesh or skeletal_mesh
                        if hasattr(tmpl, "static_mesh"):
                            mesh = tmpl.get_editor_property("static_mesh")
                            name_prop = mesh.get_name() if mesh else "None"
                        elif hasattr(tmpl, "skeletal_mesh"):
                            mesh = tmpl.get_editor_property("skeletal_mesh")
                            name_prop = mesh.get_name() if mesh else "None"
                    except Exception:
                        name_prop = "unknown"
                    unreal.log(f"DEBUG: node {n.get_name()} template mesh: {name_prop}")
            except Exception:
                pass

            # open in editor (attempt both helpers to be safe)
            try:
                unreal.EditorAssetLibrary.open_editor_for_assets([bp])
            except Exception:
                try:
                    unreal.EditorUtilityLibrary.open_editor_for_asset(bp)
                except Exception:
                    pass

            unreal.log(f"✅ Created '{bp.get_name()}' (mesh '{asset.get_name()}').")

        except Exception as e:
            unreal.log_warning(f"⚠️ Error creating BP for {asset.get_name()}: {e}")
