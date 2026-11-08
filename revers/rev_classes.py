#!/usr/bin/env python3
"""
rev_classes.py - verify/extract Projectile, AttackEntity and PlayerModel for
Rust build 26140533.

Same rules as rev_baseplayer.py: a number is never invented.  The offsets in
EXPECTED come from the request; every one is cross-checked against the evidence
that already exists for this exact build:

  * src/generated/Offsets.generated.h   (previous LIVE dump)
  * tools/reference/names_extra.txt     (UC thread, class+offset -> name)
  * tools/reference/generation_*.txt
  * tools/reference/cheatoffsets_*.txt
  * src/generated/NameOverrides.generated.h (%hash -> name)
  * live metadata declaration order + hashes (tools/meta_rva.py)

Status per field:
  MATCH        evidence has the same name at the same offset
  NAME-DIFF    offset exists, evidence calls it something else
  OFFSET-ONLY  only the offset is backed (no name at that slot)
  MISSING      no evidence at that offset

Outputs (revers/out/):
  Projectile_offsets.h / AttackEntity_offsets.h / PlayerModel_offsets.h
  classes_verify.json
  classes_report.md

Usage:
    py -3 revers\\rev_classes.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)

import rev_baseplayer as rb  # noqa: E402

# (field, offset, declared type from the request)
EXPECTED = {
    "Projectile": [
        ("initialVelocity", 0x28, "Vector3"),
        ("drag", 0x34, "float"),
        ("gravityModifier", 0x38, "float"),
        ("thickness", 0x3C, "float"),
        ("changeInitialOrientation", 0x40, "bool"),
        ("initialDistance", 0x44, "float"),
        ("initialOrientation", 0x48, "Vector3"),
        ("remainInWorld", 0x54, "bool"),
        ("stickProbability", 0x58, "float"),
        ("breakProbability", 0x5C, "float"),
        ("conditionLoss", 0x60, "float"),
        ("ricochetChance", 0x64, "float"),
        ("penetrationPower", 0x68, "float"),
        ("canRefract", 0x6C, "bool"),
        ("penetratesVehicles", 0x6D, "bool"),
        ("waterIntegrityLoss", 0x70, "float"),
        ("damageProperties", 0x78, "DamageProperties"),
        ("damageDistances", 0x80, "MinMax"),
        ("minMax", 0x80, "MinMax (live alias)"),
        ("damageMultipliers", 0x88, "MinMax"),
        ("damageTypes", 0x90, "List<DamageTypeEntry>"),
        ("rendererToScale", 0x98, "ScaleRenderer"),
        ("scaleTrailRenderer", 0x98, "ScaleTrailRenderer (live alias)"),
        ("firstPersonRenderer", 0xA0, "ScaleRenderer"),
        ("scaleTransform", 0xA0, "ScaleTransform (live alias)"),
        ("createDecals", 0xA8, "bool"),
        ("doHitEffects", 0xA9, "bool"),
        ("flybySound", 0xB0, "SoundDefinition"),
        ("soundDefinition", 0xB0, "SoundDefinition (live alias)"),
        ("flybySoundDistance", 0xB8, "float"),
        ("closeFlybySound", 0xC0, "SoundDefinition"),
        ("closeFlybyDistance", 0xC8, "float"),
        ("tumbleSpeed", 0xCC, "float"),
        ("tumbleAxis", 0xD0, "Vector3"),
        ("playDefaultHitEffects", 0xDC, "bool"),
        ("clientEffectData", 0xE0, "CustomEffectData"),
        ("customEffectData", 0xE0, "CustomEffectData (live alias)"),
        ("clientEffectPrefab", 0xE8, "GameObjectRef"),
        ("gameObjectRef", 0xE8, "GameObjectRef (live alias)"),
        ("swimScale", 0xF0, "Vector3"),
        ("swimSpeed", 0xFC, "Vector3"),
        ("baseProjectile", 0x110, "BaseProjectile"),
        ("projectile", 0x118, "Projectile"),
        ("hidden_ccfe34b7cfa107117310af889ea8338a5bf48454", 0x120,
         "%ccfe34b7 (HitTest)"),
        ("maxDistance", 0x140, "float"),
        ("currentVelocity", 0x164, "Vector3"),
        ("currentPosition", 0x170, "Vector3"),
        ("traveledDistance", 0x17C, "float"),
        ("traveledTime", 0x180, "float"),
        ("sentPosition", 0x188, "Vector3"),
        ("previousPosition", 0x194, "Vector3"),
        ("previousVelocity", 0x1A0, "Vector3"),
        ("previousTraveledTime", 0x1AC, "float"),
        ("mod", 0x1E0, "ItemModProjectile"),
        ("owner", 0x1F0, "BasePlayer"),
    ],
    "AttackEntity": [
        ("deployDelay", 0x2F0, "float"),
        ("repeatDelay", 0x2F4, "float"),
        ("animationDelay", 0x2F8, "float"),
        ("effectiveRange", 0x2FC, "float"),
        ("npcDamageScale", 0x300, "float"),
        ("attackLengthMin", 0x304, "float"),
        ("attackLengthMax", 0x308, "float"),
        ("attackSpacing", 0x30C, "float"),
        ("aiAimSwayOffset", 0x310, "float"),
        ("aiAimCone", 0x314, "float"),
        ("aiOnlyInRange", 0x318, "bool"),
        ("CloseRangeAddition", 0x31C, "float"),
        ("MediumRangeAddition", 0x320, "float"),
        ("LongRangeAddition", 0x324, "float"),
        ("CanUseAtMediumRange", 0x328, "bool"),
        ("CanUseAtLongRange", 0x329, "bool"),
        ("reloadSounds", 0x330, "SoundDefinition[]"),
        ("thirdPersonMeleeSound", 0x338, "SoundDefinition"),
        ("recoilCompDelayOverride", 0x340, "float"),
        ("wantsRecoilComp", 0x344, "bool"),
        ("showCrosshairOnTutorial", 0x345, "bool"),
        ("noHeadshots", 0x346, "bool"),
    ],
    "PlayerModel": [
        ("Shoulders", 0x98, "Transform[]"),
        ("AdditionalSpineBones", 0xA0, "Transform[]"),
        ("_multiMesh", 0xB8, "SkinnedMultiMesh"),
        ("TurnAimSmoothTime", 0xD0, "float"),
        ("TurnHead", 0xD4, "TurnSegment"),
        ("TurnChest", 0xE4, "TurnSegment"),
        ("TurnSpine", 0xF4, "TurnSegment"),
        ("TurnPelvis", 0x104, "TurnSegment"),
        ("TurnChestLowerShare", 0x114, "float"),
        ("TurnSpineLowerShare", 0x118, "float"),
        ("TurnHeadLockAngle", 0x11C, "float"),
        ("TurnHeadSmoothTime", 0x120, "float"),
        ("TurnHeadMaxSpeed", 0x124, "float"),
        ("TurnHeadAimFadeSpeed", 0x128, "float"),
        ("TurnClips", 0x130, "TurnClipSet"),
        ("TurnSpeedByBacklog", 0x138, "AnimationCurve"),
        ("TurnMoveThreshold", 0x140, "float"),
        ("TurnSuppressProceduralLegs", 0x144, "bool"),
        ("TurnLegBlendTime", 0x148, "float"),
        ("TurnPelvisEnabled", 0x14C, "bool"),
        ("TurnPelvisFootPinWeight", 0x150, "float"),
        ("TurnArmFadeSpeed", 0x154, "float"),
        ("TurnArmFadeWeight", 0x158, "float"),
        ("collision", 0x210, "BoxCollider"),
        ("censorshipCube", 0x218, "GameObject"),
        ("censorshipCubeBreasts", 0x220, "GameObject"),
        ("jawBone", 0x228, "GameObject"),
        ("neckBone", 0x230, "GameObject"),
        ("headBone", 0x238, "GameObject"),
        ("leftEye", 0x240, "GameObject"),
        ("rightEye", 0x248, "GameObject"),
        ("eyeController", 0x250, "EyeController"),
        ("blinkController", 0x258, "EyeBlink"),
        ("SpineBones", 0x260, "Transform[]"),
        ("leftFootBone", 0x268, "Transform"),
        ("rightFootBone", 0x270, "Transform"),
        ("leftHandPropBone", 0x278, "Transform"),
        ("rightHandPropBone", 0x280, "Transform"),
        ("rightHandTarget", 0x288, "Vector3"),
        ("leftClavicleBone", 0x298, "Transform"),
        ("isPreview", 0x2A0, "bool"),
        ("leftHandTargetPosition", 0x2A4, "Vector3"),
        ("leftHandTargetRotation", 0x2B0, "Quaternion"),
        ("rightHandTargetPosition", 0x2C0, "Vector3"),
        ("rightHandTargetRotation", 0x2CC, "Quaternion"),
        ("leftUlnaTwistBone", 0x2E0, "Transform"),
        ("rightUlnaTwistBone", 0x2E8, "Transform"),
        ("leftHandTwistRelaxWeight", 0x2F0, "float"),
        ("rightHandTwistRelaxWeight", 0x2F4, "float"),
        ("TwistBones", 0x2F8, "PlayerTwistBoneSetup[]"),
        ("steeringTargetDegrees", 0x300, "float"),
        ("playerBoatSteeringTargetDegrees", 0x304, "float"),
        ("rightFootTargetPosition", 0x308, "Vector3"),
        ("rightFootTargetRotation", 0x314, "Quaternion"),
        ("leftFootTargetPosition", 0x324, "Vector3"),
        ("leftFootTargetRotation", 0x330, "Quaternion"),
        ("legsAnimator", 0x340, "LegsAnimator"),
        ("upperBodyMask", 0x348, "AvatarMask"),
        ("fullMask", 0x350, "AvatarMask"),
        ("CinematicAnimationController", 0x358, "RuntimeAnimatorController"),
        ("DefaultAvatar", 0x360, "Avatar"),
        ("CinematicAvatar", 0x368, "Avatar"),
        ("DefaultHoldType", 0x370, "RuntimeAnimatorController"),
        ("SleepGesture", 0x378, "RuntimeAnimatorController"),
        ("CrawlToIncapacitatedGesture", 0x380, "RuntimeAnimatorController"),
        ("CrawlToIncapacitatedGestureHandcuff", 0x388, "RuntimeAnimatorController"),
        ("StandToIncapacitatedGesture", 0x390, "RuntimeAnimatorController"),
        ("MaleSkin", 0x3A0, "SkinSetCollection"),
        ("FemaleSkin", 0x3A8, "SkinSetCollection"),
        ("MannequinSkin", 0x3B0, "SkinSetCollection"),
        ("subsurfaceProfile", 0x3B8, "SubsurfaceProfile"),
        ("voiceVolume", 0x3C0, "float"),
        ("skinColor", 0x3C4, "float"),
        ("skinNumber", 0x3C8, "float"),
        ("meshNumber", 0x3CC, "float"),
        ("meshSubNumber", 0x3D0, "float"),
        ("hairNumber", 0x3D4, "float"),
        ("dyeNumber", 0x3D8, "float"),
        ("skinType", 0x3DC, "int"),
        ("mouthFlapPosRange", 0x3E0, "float"),
        ("mouthFlapRotRange", 0x3E4, "float"),
        ("mouthSidePosRange", 0x3E8, "float"),
        ("mouthSideFrequency", 0x3EC, "float"),
        ("ArmMotionWeight", 0x3F0, "float"),
        ("ArmGravity", 0x3F4, "float"),
        ("ArmGravityByPitch", 0x3F8, "AnimationCurve"),
        ("ArmStiffness", 0x400, "float"),
        ("ArmDamping", 0x404, "float"),
        ("ArmMotionSpeedLimit", 0x408, "float"),
        ("ArmFlexAngle", 0x40C, "float"),
        ("ArmFlexByPitch", 0x410, "AnimationCurve"),
        ("ArmSpinFadeStart", 0x418, "float"),
        ("ArmSpinFadeEnd", 0x41C, "float"),
        ("SpineLookUpLimit", 0x420, "float"),
        ("SpineTwistClamp", 0x424, "float"),
        ("SpineHeadLookWeightVertical", 0x428, "float"),
        ("HeadYawLimit", 0x42C, "float"),
        ("SpineLowerFollow", 0x430, "float"),
        ("SpineFollowSmoothSpeed", 0x434, "float"),
        ("movementSounds", 0x438, "MovementSounds"),
        ("showSash", 0x440, "bool"),
        ("tempPoseType", 0x444, "int"),
        ("underwearSkin", 0x448, "uint"),
        ("position", 0x488, "Vector3"),
        ("animator", 0x678, "Animator"),
        ("modelState", 0x6D8, "%d5d14770"),
    ],
}


def verify_class(name, rows, ev_obj):
    ev = rb.evidence_for_class(ev_obj, name)
    aliases = rb.aliases_for_class(ev_obj, name)
    names_at = {}
    for f, o, _t in rows:
        names_at.setdefault(o, set()).add(rb.norm(f))
    out = []
    for field, off, typ in rows:
        hit = ev.get(off)
        if hit and rb.norm(hit[0]) == rb.norm(field):
            status = "MATCH"
        elif hit and rb.norm(hit[0]) in names_at.get(off, set()):
            # the same offset is requested under two accepted names
            status = "ALIAS"
        elif hit:
            status = "NAME-DIFF"
        elif off in aliases.get(rb.norm(field), set()):
            status = "NAME-ONLY"
        else:
            status = "MISSING"
        out.append({
            "field": field,
            "offset": off,
            "type": typ,
            "evidence_name": hit[0] if hit else "",
            "evidence_type": hit[1] if hit else "",
            "status": status,
        })
    return out


def main():
    ev_obj = rb.build_evidence()
    os.makedirs(OUT, exist_ok=True)

    report = ["# Projectile / AttackEntity / PlayerModel - build 26140533", "",
              "Cross-check of the requested offsets against every evidence source "
              "for this build.", ""]
    summary = {}

    for name, rows in EXPECTED.items():
        res = verify_class(name, rows, ev_obj)
        counts = {}
        for r in res:
            counts[r["status"]] = counts.get(r["status"], 0) + 1

        # header
        h = [
            "// ===========================================================================",
            f"//  {name}_offsets.h - Rust build 26140533",
            "//  generated by revers/rev_classes.py - DO NOT EDIT BY HAND",
            "//  each offset is cross-checked against the live dump / reference "
            "evidence",
            "// ===========================================================================",
            "#pragma once",
            "#include <cstdint>",
            "",
            f"namespace {name}",
            "{",
        ]
        for r in res:
            note = f" // {r['type']}"
            if r["status"] != "MATCH":
                note += f" [{r['status']}"
                if r["evidence_name"]:
                    note += f": {r['evidence_name']}"
                note += "]"
            h.append(f"    constexpr std::uintptr_t {r['field']:44s} = "
                     f"0x{r['offset']:X};{note}")
        h.append("}")
        with open(os.path.join(OUT, f"{name}_offsets.h"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("\n".join(h) + "\n")

        summary[name] = counts
        report.append(f"## {name}\n")
        report.append(f"- fields: **{len(res)}**")
        for k in ("MATCH", "ALIAS", "NAME-DIFF", "NAME-ONLY", "MISSING"):
            if counts.get(k):
                report.append(f"- {k}: **{counts[k]}**")
        report.append("")
        report.append("| field | offset | type | evidence | status |")
        report.append("|---|---|---|---|---|")
        for r in res:
            report.append(f"| `{r['field']}` | `0x{r['offset']:X}` | {r['type']} | "
                          f"{('`' + r['evidence_name'] + '`') if r['evidence_name'] else '-'} | "
                          f"{r['status']} |")
        report.append("")

    data = {"build": "26140533",
            "classes": {k: verify_class(k, v, ev_obj) for k, v in EXPECTED.items()},
            "summary": summary}
    with open(os.path.join(OUT, "classes_verify.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
    with open(os.path.join(OUT, "classes_report.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report) + "\n")

    for name in EXPECTED:
        print(f"[+] {name:<14} {summary[name]}")
        print(f"    -> {os.path.join(OUT, name + '_offsets.h')}")
    print(f"[+] wrote {os.path.join(OUT, 'classes_report.md')}")
    print(f"[+] wrote {os.path.join(OUT, 'classes_verify.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
